#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
AL-MĪZĀN v5.0 — MASSIVE CORPUS HARVESTER
Protocole Mouhaqqiq — Extraction Totale du Corpus Hadith Salaf
════════════════════════════════════════════════════════════════════════════
Conforme à Constitution_v4.md (Version 5.0 Unifiée)
Mode Autonome Total — Jamais d'arrêt — Jamais de question
════════════════════════════════════════════════════════════════════════════
"""

import hashlib
import sqlite3
import requests
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION GLOBALE
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent / "almizane.db"
LOG_FILE = Path(__file__).parent / "harvest.log"
PROGRESS_FILE = Path(__file__).parent.parent / "output" / "HARVESTING_LIVE_STATUS.md"

# Configuration du logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8'
)

# ═══════════════════════════════════════════════════════════════════════════
# TIER 1 — SOURCES OFFICIELLES DE MÉDINE
# ═══════════════════════════════════════════════════════════════════════════

DORAR_API = "https://dorar.net/dorar_api.json"
HADEETHENC_API = "https://hadeethenc.com/api/v1/hadeeths/list/"

# ═══════════════════════════════════════════════════════════════════════════
# COLLECTIONS À ÉPUISER (KUTUB AL-SITTA + MASANID)
# ═══════════════════════════════════════════════════════════════════════════

COLLECTIONS = [
    # KUTUB AL-SITTA (Priorité Absolue)
    "صحيح البخاري",
    "صحيح مسلم",
    "سنن أبي داود",
    "جامع الترمذي",
    "سنن النسائي",
    "سنن ابن ماجه",
    
    # MASANID
    "مسند أحمد",
    "مسند الحميدي",
    "مسند الطيالسي",
    "مسند عبد الرزاق",
    "مسند ابن أبي شيبة",
    
    # SAHIHAT
    "صحيح ابن حبان",
    "صحيح ابن خزيمة",
    "المستدرك للحاكم",
    
    # SUNAN / JAWAMI'
    "سنن الدارقطني",
    "السنن الكبرى للبيهقي",
    "السنن الصغرى للبيهقي",
    "سنن الدارمي",
    "موطأ مالك",
    "سنن سعيد بن منصور",
    
    # MAWSOU'AT
    "المعجم الكبير للطبراني",
    "المعجم الأوسط للطبراني",
    "المعجم الصغير للطبراني",
    "مصنف عبد الرزاق",
    "مصنف ابن أبي شيبة",
    "شعب الإيمان للبيهقي",
    "حلية الأولياء لأبي نعيم",
    
    # KUTUB ZIYADAT
    "الأدب المفرد للبخاري",
    "رياض الصالحين للنووي",
    "الأربعين النووية",
    "مشكاة المصابيح للتبريزي",
    "بلوغ المرام لابن حجر",
    "المنتقى لابن الجارود"
]

# ═══════════════════════════════════════════════════════════════════════════
# SPECTRE D'AUTHENTICITÉ COMPLET
# ═══════════════════════════════════════════════════════════════════════════

GRADE_MAP = {
    # MAQBUL
    "صحيح": ("Sahih", "MAQBUL", 0),
    "صحيح لغيره": ("Sahih Ghayri", "MAQBUL", 0),
    "حسن": ("Hasan", "MAQBUL", 0),
    "حسن لغيره": ("Hasan Ghayri", "MAQBUL", 0),
    
    # DAIF
    "ضعيف": ("Da'if", "DAIF", 0),
    "ضعيف جداً": ("Da'if Jiddan", "DAIF", 0),
    "ضعيف جدا": ("Da'if Jiddan", "DAIF", 0),
    "منكر": ("Munkar", "DAIF", 0),
    "شاذ": ("Shaadh", "DAIF", 0),
    "متروك": ("Matruk", "DAIF", 0),
    
    # MAWDUU (Badge Rouge Obligatoire)
    "موضوع": ("Mawdu'", "MAWDUU", 1),
    "باطل": ("Batil", "MAWDUU", 1),
    
    # Variantes orthographiques
    "صحيح الإسناد": ("Sahih", "MAQBUL", 0),
    "حسن الإسناد": ("Hasan", "MAQBUL", 0),
    "إسناده صحيح": ("Sahih", "MAQBUL", 0),
    "إسناده حسن": ("Hasan", "MAQBUL", 0),
}

# ═══════════════════════════════════════════════════════════════════════════
# LEXIQUE DE FER (Attributs Divins)
# ═══════════════════════════════════════════════════════════════════════════

LEXIQUE_FER = {
    'استوى': ('S\'est établi (par Son Essence)', 'S\'est installé / a pris le contrôle'),
    'يد': ('Main (réelle, sans comparaison)', 'Puissance / Grâce'),
    'نزول': ('Descend (comme Il le mérite)', 'Sa miséricorde descend'),
    'وجه': ('Visage (réel, sans comparaison)', 'Essence / Être'),
    'ساق': ('Jambe (réelle, sans comparaison)', 'Sévérité / Épreuve'),
    'عين': ('Œil/Regard (réel, sans comparaison)', 'Connaissance / Surveillance'),
}

# ═══════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

class MassiveCorpusHarvester:
    """Harvester massif conforme Constitution v5.0"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.stats = {
            'total_attempted': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'mawduu_detected': 0,
            'taawil_detected': 0,
            'by_collection': {},
            'by_grade': {},
            'start_time': datetime.now().isoformat()
        }
        
        # Créer le dossier output si nécessaire
        PROGRESS_FILE.parent.mkdir(exist_ok=True)
        
        logging.info("="*80)
        logging.info("DÉMARRAGE HARVESTER MASSIF AL-MĪZĀN v5.0")
        logging.info("="*80)
    
    def sha256_matn(self, matn_ar: str) -> str:
        """Génère le Sanad Numérique (hash SHA256 du matn arabe)"""
        return hashlib.sha256(matn_ar.strip().encode('utf-8')).hexdigest()
    
    def apply_lexique_fer(self, matn_fr: str, matn_ar: str) -> Tuple[str, bool]:
        """
        Applique le Lexique de Fer sur la traduction française
        Retourne: (traduction_corrigée, taawil_detected)
        """
        if not matn_fr:
            return matn_fr, False
        
        taawil_detected = False
        corrected = matn_fr
        
        for terme_ar, (terme_correct, terme_interdit) in LEXIQUE_FER.items():
            if terme_ar in matn_ar:
                # Vérifier si la traduction interdite est présente
                if terme_interdit.lower() in corrected.lower():
                    taawil_detected = True
                    logging.warning(f"TAAWIL_DETECTED | terme={terme_ar} | interdit={terme_interdit}")
                    # Remplacer par la traduction correcte
                    corrected = corrected.replace(terme_interdit, terme_correct)
        
        return corrected, taawil_detected
    
    def parse_grade(self, grade_raw: str) -> Tuple[str, str, int]:
        """
        Parse le grade depuis l'API et retourne (grade_final, categorie, badge_alerte)
        """
        if not grade_raw:
            return ("Inconnu", "DAIF", 0)
        
        grade_clean = grade_raw.strip()
        
        # Recherche exacte
        if grade_clean in GRADE_MAP:
            return GRADE_MAP[grade_clean]
        
        # Recherche partielle (pour variantes)
        for key, value in GRADE_MAP.items():
            if key in grade_clean:
                return value
        
        # Par défaut
        logging.warning(f"GRADE_UNKNOWN | grade_raw={grade_raw}")
        return ("Inconnu", "DAIF", 0)
    
    def harvest_collection(self, conn: sqlite3.Connection, collection_name: str) -> int:
        """
        Extrait tous les hadiths d'une collection depuis Dorar.net
        Retourne le nombre de hadiths insérés
        """
        page = 1
        total_inserted = 0
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        logging.info(f"DÉBUT COLLECTION | {collection_name}")
        
        while True:
            # Protection contre boucle infinie
            if consecutive_errors >= max_consecutive_errors:
                logging.error(f"ARRÊT COLLECTION | {collection_name} | trop d'erreurs consécutives")
                break
            
            try:
                # Requête API Dorar
                response = requests.get(
                    DORAR_API,
                    params={
                        "skey": collection_name,
                        "lang": "ar",
                        "page": page
                    },
                    timeout=15
                )
                
                if response.status_code != 200:
                    logging.error(f"API_ERROR | {collection_name} | page={page} | status={response.status_code}")
                    consecutive_errors += 1
                    time.sleep(2)
                    continue
                
                data = response.json()
                results = data.get("ahadith", [])
                
                # Si pas de résultats, fin de la collection
                if not results:
                    logging.info(f"FIN COLLECTION | {collection_name} | total={total_inserted}")
                    break
                
                # Reset compteur d'erreurs
                consecutive_errors = 0
                
                # Traiter chaque hadith
                for h in results:
                    self.stats['total_attempted'] += 1
                    
                    matn_ar = h.get("hadith", "").strip()
                    if not matn_ar:
                        continue
                    
                    # Générer SHA256
                    sha = self.sha256_matn(matn_ar)
                    
                    # Parser le grade
                    grade_raw = h.get("grade", "")
                    grade_final, categorie, badge = self.parse_grade(grade_raw)
                    
                    # Traduction française (si disponible)
                    matn_fr = h.get("translation_fr", "")
                    
                    # Appliquer Lexique de Fer
                    if matn_fr:
                        matn_fr, taawil = self.apply_lexique_fer(matn_fr, matn_ar)
                        if taawil:
                            self.stats['taawil_detected'] += 1
                    
                    # Détecter Mawdū'
                    if badge == 1:
                        self.stats['mawduu_detected'] += 1
                    
                    try:
                        # Insertion dans la base
                        conn.execute("""
                            INSERT OR IGNORE INTO hadiths
                            (sha256, collection, numero_hadith, livre, chapitre,
                             matn_ar, matn_fr, isnad_brut, grade_final, categorie, 
                             badge_alerte, source_url, source_api)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, (
                            sha,
                            collection_name,
                            h.get("rnum", ""),
                            h.get("book", ""),
                            h.get("chapter", ""),
                            matn_ar,
                            matn_fr,
                            h.get("isnad", ""),
                            grade_final,
                            categorie,
                            badge,
                            h.get("link", ""),
                            "dorar_json"
                        ))
                        
                        if conn.total_changes > 0:
                            total_inserted += 1
                            self.stats['total_inserted'] += 1
                            
                            # Stats par grade
                            self.stats['by_grade'][grade_final] = self.stats['by_grade'].get(grade_final, 0) + 1
                        else:
                            self.stats['total_duplicates'] += 1
                        
                        conn.commit()
                        
                    except Exception as e:
                        logging.error(f"INSERT_ERROR | sha={sha} | {e}")
                        self.stats['total_errors'] += 1
                
                # Rapport de progression tous les 500 hadiths
                if total_inserted > 0 and total_inserted % 500 == 0:
                    self.print_progress_report(collection_name, total_inserted)
                
                # Page suivante
                page += 1
                
                # Adab numérique (respecter les serveurs)
                time.sleep(1.0)
                
            except requests.exceptions.Timeout:
                logging.error(f"TIMEOUT | {collection_name} | page={page}")
                consecutive_errors += 1
                time.sleep(3)
                
            except Exception as e:
                logging.error(f"EXCEPTION | {collection_name} | page={page} | {e}")
                consecutive_errors += 1
                time.sleep(2)
        
        # Stats par collection
        self.stats['by_collection'][collection_name] = total_inserted
        
        return total_inserted
    
    def print_progress_report(self, collection: str, count: int):
        """Affiche et log un rapport de progression"""
        report = f"""
┌──────────────────────────────────────────┐
│ [RAPPORT #{count}] Collection : {collection[:20]}
│ Hadiths insérés : {count}
│ Mawdū' détectés : {self.stats['mawduu_detected']} (⚠️ badge rouge)
│ Erreurs Aqida  : {self.stats['taawil_detected']} (voir harvest.log)
└──────────────────────────────────────────┘
"""
        print(report)
        logging.info(f"PROGRESS | {collection} | {count}")
        
        # Mise à jour du fichier de statut live
        self.update_live_status()
    
    def update_live_status(self):
        """Met à jour le fichier de statut en temps réel"""
        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        rate = self.stats['total_inserted'] / max(elapsed / 60, 1)  # hadiths/minute
        
        status = f"""# 🕌 HARVESTING EN COURS — AL-MĪZĀN v5.0

**Dernière mise à jour:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Statistiques Globales

- **Tentatives totales:** {self.stats['total_attempted']:,}
- **Hadiths insérés:** {self.stats['total_inserted']:,}
- **Doublons ignorés:** {self.stats['total_duplicates']:,}
- **Erreurs:** {self.stats['total_errors']:,}
- **Mawdū' détectés:** {self.stats['mawduu_detected']:,} ⚠️
- **Ta'wil détectés:** {self.stats['taawil_detected']:,} ⚠️

## ⚡ Performance

- **Vitesse:** {rate:.1f} hadiths/minute
- **Durée écoulée:** {int(elapsed // 60)} minutes

## 📚 Par Collection

"""
        for coll, count in sorted(self.stats['by_collection'].items(), key=lambda x: x[1], reverse=True):
            status += f"- **{coll}:** {count:,} hadiths\n"
        
        status += f"""
## 📈 Par Grade

"""
        for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
            status += f"- **{grade}:** {count:,}\n"
        
        status += f"""
---

*Mode Autonome Total — Extraction en cours...*
"""
        
        PROGRESS_FILE.write_text(status, encoding='utf-8')
    
    def run(self):
        """Point d'entrée principal — Mode Autonome Total"""
        print("="*80)
        print("🕌 AL-MĪZĀN v5.0 — MASSIVE CORPUS HARVESTER")
        print("="*80)
        print("Mode: AUTONOME TOTAL")
        print("Arrêt: UNIQUEMENT quand toutes sources épuisées à 100%")
        print("="*80)
        
        # Connexion DB
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        
        grand_total = 0
        
        try:
            # Parcourir toutes les collections
            for i, collection in enumerate(COLLECTIONS, 1):
                print(f"\n🕌 [{i}/{len(COLLECTIONS)}] Début : {collection}")
                logging.info(f"START_COLLECTION | {collection}")
                
                n = self.harvest_collection(conn, collection)
                grand_total += n
                
                print(f"✅ {collection} terminé : {n:,} hadiths")
                logging.info(f"DONE_COLLECTION | {collection} | total={n}")
                
                # Pause entre collections (adab numérique)
                time.sleep(2)
            
            # Rapport final
            self.stats['end_time'] = datetime.now().isoformat()
            self.print_final_report(grand_total)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ INTERRUPTION MANUELLE")
            logging.warning("MANUAL_INTERRUPT")
            self.print_final_report(grand_total)
            
        except Exception as e:
            print(f"\n\n❌ ERREUR CRITIQUE: {e}")
            logging.error(f"CRITICAL_ERROR | {e}")
            self.print_final_report(grand_total)
            
        finally:
            conn.close()
    
    def print_final_report(self, grand_total: int):
        """Affiche le rapport final"""
        elapsed = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        
        report = f"""

{'='*80}
📚 EXTRACTION COMPLÈTE — RAPPORT FINAL
{'='*80}

📊 STATISTIQUES GLOBALES
   • Tentatives totales    : {self.stats['total_attempted']:,}
   • Hadiths insérés       : {self.stats['total_inserted']:,}
   • Doublons ignorés      : {self.stats['total_duplicates']:,}
   • Erreurs               : {self.stats['total_errors']:,}
   • Mawdū' détectés       : {self.stats['mawduu_detected']:,} ⚠️
   • Ta'wil détectés       : {self.stats['taawil_detected']:,} ⚠️

⏱️  PERFORMANCE
   • Durée totale          : {int(elapsed // 60)} minutes
   • Vitesse moyenne       : {self.stats['total_inserted'] / max(elapsed / 60, 1):.1f} hadiths/minute

📚 TOP 10 COLLECTIONS
"""
        for coll, count in sorted(self.stats['by_collection'].items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"   • {coll[:40]:40s} : {count:6,} hadiths\n"
        
        report += f"""
📈 RÉPARTITION PAR GRADE
"""
        for grade, count in sorted(self.stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
            pct = count / max(self.stats['total_inserted'], 1) * 100
            report += f"   • {grade:20s} : {count:6,} ({pct:5.1f}%)\n"
        
        report += f"""
{'='*80}
✅ MISSION ACCOMPLIE
   Base de données : {self.db_path}
   Log complet     : {LOG_FILE}
   Statut live     : {PROGRESS_FILE}
{'='*80}
"""
        
        print(report)
        logging.info("GRAND_TOTAL=" + str(grand_total))
        logging.info("MISSION_COMPLETE")
        
        # Sauvegarder le rapport final
        report_file = PROGRESS_FILE.parent / "HARVESTING_FINAL_REPORT.md"
        report_file.write_text(report, encoding='utf-8')
        print(f"\n💾 Rapport final sauvegardé : {report_file}")

# ═══════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal"""
    harvester = MassiveCorpusHarvester()
    harvester.run()

if __name__ == "__main__":
    main()