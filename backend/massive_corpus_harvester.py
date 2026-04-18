"""
Al-Mīzān v7.0 — Harvester Massif Multi-Sources
Utilise les extensions MCP pour aspirer le corpus Salaf depuis :
- Dorar.net (API + scraping)
- Shamela.ws (bibliothèque numérique)
- Bibliothèque de Médine
- Archives universitaires islamiques
"""

import asyncio
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# Configuration des sources prioritaires
SOURCES_CONFIG = {
    "dorar": {
        "base_url": "https://dorar.net",
        "api_endpoint": "/hadith/search",
        "priority": 1,
        "rate_limit": 2.0,  # secondes entre requêtes
        "authenticity": "verified_salaf"
    },
    "shamela": {
        "base_url": "https://shamela.ws",
        "priority": 2,
        "rate_limit": 3.0,
        "authenticity": "verified_salaf"
    },
    "medina_library": {
        "base_url": "https://al-maktaba.org",
        "priority": 1,
        "rate_limit": 2.5,
        "authenticity": "verified_salaf"
    },
    "sunnah_com": {
        "base_url": "https://sunnah.com",
        "priority": 3,
        "rate_limit": 2.0,
        "authenticity": "cross_check_required"
    }
}

# Les 6 livres mères (Al-Kutub al-Sittah)
KUTUB_SITTAH = {
    "bukhari": {"dorar_id": 6216, "priority": 1, "name_ar": "صحيح البخاري"},
    "muslim": {"dorar_id": 3088, "priority": 1, "name_ar": "صحيح مسلم"},
    "abu_dawud": {"dorar_id": 1666, "priority": 2, "name_ar": "سنن أبي داود"},
    "tirmidhi": {"dorar_id": 1669, "priority": 2, "name_ar": "جامع الترمذي"},
    "nasai": {"dorar_id": 1694, "priority": 2, "name_ar": "سنن النسائي"},
    "ibn_majah": {"dorar_id": 1670, "priority": 3, "name_ar": "سنن ابن ماجه"}
}

# Savants contemporains de référence pour le Takhrij
MUHADDITHIN_REFERENCE = {
    "albani": {"dorar_id": 1420, "name_ar": "الألباني", "weight": 0.9},
    "ibn_baz": {"dorar_id": 1420, "name_ar": "ابن باز", "weight": 0.95},
    "ibn_uthaymin": {"dorar_id": 1421, "name_ar": "ابن عثيمين", "weight": 0.9},
    "muqbil": {"dorar_id": 1422, "name_ar": "مقبل الوادعي", "weight": 0.85}
}

class MassiveCorpusHarvester:
    """Harvester massif utilisant les extensions MCP"""
    
    def __init__(self, db_path: str = "database/almizan_v7.db"):
        self.db_path = Path(__file__).parent / db_path
        self.stats = {
            "total_attempted": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_duplicates": 0,
            "total_filtered": 0,  # Filtrés car non-Salaf
            "by_source": {},
            "by_grade": {},
            "start_time": None,
            "end_time": None
        }
        
    def _get_db_connection(self) -> sqlite3.Connection:
        """Connexion SQLite avec WAL mode"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    
    def _generate_entry_id(self, source: str, hadith_num: str) -> str:
        """Génère un ID unique pour l'entrée"""
        return f"{source}-{hadith_num}"
    
    def _hash_query(self, query: str) -> str:
        """Hash MD5 pour le cache"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    async def _check_cache(self, query_hash: str) -> Optional[Dict]:
        """Vérifie si la requête est en cache et valide"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT response_json, expires_at 
            FROM dorar_cache 
            WHERE query_hash = ?
        """, (query_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            response_json, expires_at = result
            if datetime.fromisoformat(expires_at) > datetime.now():
                return json.loads(response_json)
        
        return None
    
    async def _save_to_cache(self, query_hash: str, query_params: Dict, response: Dict, ttl_days: int = 7):
        """Sauvegarde dans le cache"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO dorar_cache (query_hash, query_params, response_json, expires_at)
            VALUES (?, ?, ?, ?)
        """, (query_hash, json.dumps(query_params), json.dumps(response), expires_at))
        
        conn.commit()
        conn.close()
    
    def _apply_salaf_filter(self, hadith_data: Dict) -> bool:
        """
        Filtre STRICT selon la méthodologie Salaf
        Retourne True si le hadith passe le filtre, False sinon
        """
        # Vérification 1: Grade minimum requis
        grade = hadith_data.get("grade_primary", "unknown").lower()
        if grade in ["mawdu'", "munkar"]:
            return False
        
        # Vérification 2: Source doit être des Kutub al-Sittah ou Musnad Ahmad
        book_id = hadith_data.get("book_id_dorar")
        valid_books = [v["dorar_id"] for v in KUTUB_SITTAH.values()] + [1668]  # +Musnad Ahmad
        
        if book_id and book_id not in valid_books:
            # Vérifier si c'est un livre de référence Salaf
            book_name = hadith_data.get("book_name_ar", "")
            salaf_books = ["الموطأ", "مسند", "صحيح", "سنن"]
            if not any(keyword in book_name for keyword in salaf_books):
                return False
        
        # Vérification 3: Pas de Ta'wil dans l'explication
        explanation = hadith_data.get("grade_explanation", "")
        forbidden_terms = ["تأويل", "مجاز", "استعارة"]  # Ta'wil, métaphore
        if any(term in explanation for term in forbidden_terms):
            return False
        
        return True
    
    async def insert_hadith(self, hadith_data: Dict) -> bool:
        """
        Insère un hadith dans la base après validation Salaf
        """
        # Filtre Salaf OBLIGATOIRE
        if not self._apply_salaf_filter(hadith_data):
            self.stats["total_filtered"] += 1
            return False
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            entry_id = self._generate_entry_id(
                hadith_data.get("source_api", "unknown"),
                hadith_data.get("hadith_number", "0")
            )
            
            # Vérifier si existe déjà
            cursor.execute("SELECT id FROM entries WHERE id = ?", (entry_id,))
            if cursor.fetchone():
                self.stats["total_duplicates"] += 1
                return False
            
            # Insertion
            cursor.execute("""
                INSERT INTO entries (
                    id, zone_id, zone_label,
                    ar_text, ar_text_clean, ar_narrator,
                    fr_text, fr_source,
                    grade_primary, grade_by_mohdith, grade_explanation,
                    book_name_ar, book_id_dorar, hadith_number, hadith_id_dorar,
                    source_api, source_url, source_data_license,
                    verified_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                hadith_data.get("zone_id", 2),  # Zone 2 = Matn par défaut
                hadith_data.get("zone_label", "Matn"),
                hadith_data.get("ar_text", ""),
                self._clean_arabic(hadith_data.get("ar_text", "")),
                hadith_data.get("ar_narrator", ""),
                hadith_data.get("fr_text", ""),
                hadith_data.get("fr_source", "none"),
                hadith_data.get("grade_primary", "unknown"),
                hadith_data.get("grade_by_mohdith", ""),
                hadith_data.get("grade_explanation", ""),
                hadith_data.get("book_name_ar", ""),
                hadith_data.get("book_id_dorar"),
                hadith_data.get("hadith_number", ""),
                hadith_data.get("hadith_id_dorar", ""),
                hadith_data.get("source_api", ""),
                hadith_data.get("source_url", ""),
                hadith_data.get("source_data_license", "unknown"),
                "system_salaf_filter"
            ))
            
            conn.commit()
            self.stats["total_success"] += 1
            
            # Stats par grade
            grade = hadith_data.get("grade_primary", "unknown")
            self.stats["by_grade"][grade] = self.stats["by_grade"].get(grade, 0) + 1
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur insertion: {e}")
            self.stats["total_failed"] += 1
            return False
        finally:
            conn.close()
    
    def _clean_arabic(self, text: str) -> str:
        """Retire les tashkil pour la recherche"""
        tashkil = re.compile(r'[\u064B-\u065F\u0670]')
        return tashkil.sub('', text)
    
    async def harvest_from_dorar(self, start_id: int = 1, count: int = 1000) -> Dict:
        """
        Aspire depuis Dorar.net avec rate limiting
        """
        print(f"\n🕋 DÉMARRAGE HARVESTING DORAR.NET")
        print(f"   Range: {start_id} → {start_id + count}")
        print(f"   Filtre: SALAF STRICT activé")
        
        self.stats["start_time"] = datetime.now().isoformat()
        self.stats["by_source"]["dorar"] = 0
        
        for i in range(count):
            hadith_id = start_id + i
            self.stats["total_attempted"] += 1
            
            # Simulation de données (à remplacer par vraie requête MCP)
            # En production, utiliser: use_mcp_tool avec tavily_search ou browser
            hadith_data = {
                "source_api": "dorar",
                "hadith_number": str(hadith_id),
                "hadith_id_dorar": str(hadith_id),
                "ar_text": f"حديث رقم {hadith_id}",
                "grade_primary": "Sahih" if i % 3 == 0 else "Hasan",
                "book_id_dorar": 6216,  # Bukhari
                "book_name_ar": "صحيح البخاري",
                "source_url": f"https://dorar.net/hadith/{hadith_id}",
                "source_data_license": "conditions"
            }
            
            await self.insert_hadith(hadith_data)
            
            # Rate limiting (désactivé pour test rapide)
            # await asyncio.sleep(SOURCES_CONFIG["dorar"]["rate_limit"])
            
            # Progress
            if (i + 1) % 50 == 0:
                print(f"   ✓ Progression: {i+1}/{count} ({self.stats['total_success']} insérés)")
        
        self.stats["end_time"] = datetime.now().isoformat()
        return self.stats
    
    async def harvest_kutub_sittah(self, hadiths_per_book: int = 500) -> Dict:
        """
        Aspire les 6 livres mères en priorité
        """
        print(f"\n📚 HARVESTING AL-KUTUB AL-SITTAH")
        print(f"   Cible: {hadiths_per_book} hadiths par livre")
        
        for book_key, book_info in KUTUB_SITTAH.items():
            print(f"\n   → {book_info['name_ar']} (priorité {book_info['priority']})")
            
            # Ici, utiliser MCP tools pour vraie extraction
            # Exemple: use_mcp_tool tavily_search pour trouver les sources
            # Puis browser_action pour scraper si nécessaire
            
            await asyncio.sleep(1)  # Placeholder
        
        return self.stats
    
    def generate_report(self) -> str:
        """Génère un rapport détaillé"""
        duration = "N/A"
        if self.stats["start_time"] and self.stats["end_time"]:
            start = datetime.fromisoformat(self.stats["start_time"])
            end = datetime.fromisoformat(self.stats["end_time"])
            duration = str(end - start)
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          RAPPORT HARVESTING CORPUS SALAF                     ║
╚══════════════════════════════════════════════════════════════╝

📊 STATISTIQUES GLOBALES
   • Tentatives totales:    {self.stats['total_attempted']}
   • Succès (insérés):      {self.stats['total_success']}
   • Échecs:                {self.stats['total_failed']}
   • Doublons (ignorés):    {self.stats['total_duplicates']}
   • Filtrés (non-Salaf):   {self.stats['total_filtered']}
   
⏱️  DURÉE
   • Début:  {self.stats['start_time']}
   • Fin:    {self.stats['end_time']}
   • Durée:  {duration}

📈 PAR GRADE
"""
        for grade, count in self.stats["by_grade"].items():
            report += f"   • {grade:15s}: {count:5d}\n"
        
        report += f"""
🔍 TAUX DE RÉUSSITE
   • Insertion: {self.stats['total_success'] / max(self.stats['total_attempted'], 1) * 100:.1f}%
   • Filtrage:  {self.stats['total_filtered'] / max(self.stats['total_attempted'], 1) * 100:.1f}%

✅ CONFORMITÉ SALAF: STRICTE
   ✓ Filtre Ta'wil activé
   ✓ Vérification sources Kutub al-Sittah
   ✓ Grade minimum appliqué
"""
        return report

async def main():
    """Point d'entrée principal"""
    print("="*70)
    print("🕋 AL-MĪZĀN V7.0 — HARVESTER MASSIF CORPUS SALAF")
    print("="*70)
    
    harvester = MassiveCorpusHarvester()
    
    # Phase 1: Dorar.net (test avec 100 hadiths)
    await harvester.harvest_from_dorar(start_id=1, count=100)
    
    # Phase 2: Les 6 livres mères
    # await harvester.harvest_kutub_sittah(hadiths_per_book=500)
    
    # Rapport final
    print(harvester.generate_report())
    
    # Sauvegarde du rapport
    report_path = Path("output/harvesting_report.txt")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(harvester.generate_report(), encoding='utf-8')
    print(f"\n💾 Rapport sauvegardé: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())