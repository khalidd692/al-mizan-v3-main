#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕋 AL-MĪZĀN V7.0 — HARVESTER HADEETHENC
Extraction de hadiths depuis l'API HadeethEnc.com
Alternative fonctionnelle à Dorar.net
"""

import sqlite3
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('harvest_hadeethenc.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HadeethEncHarvester:
    """Harvester pour l'API HadeethEnc.com"""
    
    BASE_URL = "https://hadeethenc.com/api/v1"
    DB_PATH = "almizane.db"
    
    # Mapping des grades acceptés (Salaf uniquement)
    VALID_GRADES = {
        'صحيح': 'sahih',
        'حسن': 'hasan',
        'صحيح لغيره': 'sahih',
        'حسن لغيره': 'hasan',
        'متفق عليه': 'sahih',  # Bukhari + Muslim = Sahih
        'رواه البخاري': 'sahih',
        'رواه مسلم': 'sahih'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Al-Mizan-Harvester/7.0'
        })
        self.stats = {
            'total_processed': 0,
            'inserted': 0,
            'skipped_grade': 0,
            'skipped_duplicate': 0,
            'errors': 0
        }
    
    def get_categories(self, lang: str = "ar") -> List[Dict]:
        """Récupère toutes les catégories"""
        try:
            url = f"{self.BASE_URL}/categories/list"
            response = self.session.get(url, params={"language": lang}, timeout=10)
            response.raise_for_status()
            
            categories = response.json()
            logger.info(f"✅ {len(categories)} catégories récupérées")
            return categories
            
        except Exception as e:
            logger.error(f"❌ Erreur get_categories: {e}")
            return []
    
    def get_hadiths_by_category(
        self, 
        category_id: int, 
        page: int = 1,
        per_page: int = 50
    ) -> Optional[Dict]:
        """Récupère les hadiths d'une catégorie (page par page)"""
        try:
            url = f"{self.BASE_URL}/hadeeths/list"
            params = {
                "language": "ar",
                "category_id": category_id,
                "page": page,
                "per_page": per_page
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Erreur get_hadiths_by_category: {e}")
            return None
    
    def get_hadith_details(self, hadith_id: int) -> Optional[Dict]:
        """Récupère les détails complets d'un hadith"""
        try:
            url = f"{self.BASE_URL}/hadeeths/one"
            params = {
                "language": "ar",
                "id": hadith_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Erreur get_hadith_details (ID {hadith_id}): {e}")
            return None
    
    def is_valid_grade(self, grade: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si le grade est accepté selon la méthodologie Salaf
        
        Returns:
            (is_valid, normalized_grade)
        """
        if not grade:
            return False, None
        
        grade = grade.strip()
        
        # Vérifier si le grade est dans notre liste acceptée
        for valid_grade, normalized in self.VALID_GRADES.items():
            if valid_grade in grade:
                return True, normalized
        
        return False, None
    
    def hadith_exists(self, conn: sqlite3.Connection, hadith_text: str) -> bool:
        """Vérifie si un hadith existe déjà dans la base"""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM entries WHERE hadith_ar = ?",
            (hadith_text,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    
    def insert_hadith(
        self, 
        conn: sqlite3.Connection, 
        hadith_data: Dict
    ) -> bool:
        """Insère un hadith dans la base v7"""
        try:
            # Extraire les données
            hadith_text = hadith_data.get('hadeeth', '').strip()
            grade_ar = hadith_data.get('grade', '').strip()
            attribution = hadith_data.get('attribution', '').strip()
            explanation = hadith_data.get('explanation', '').strip()
            
            # Valider le grade
            is_valid, grade_normalized = self.is_valid_grade(grade_ar)
            if not is_valid:
                self.stats['skipped_grade'] += 1
                logger.debug(f"⏭️  Grade non accepté: {grade_ar}")
                return False
            
            # Vérifier les doublons
            if self.hadith_exists(conn, hadith_text):
                self.stats['skipped_duplicate'] += 1
                logger.debug(f"⏭️  Hadith déjà présent")
                return False
            
            # Déterminer la source (livre)
            source = "HadeethEnc"
            if "البخاري" in attribution:
                source = "Sahih al-Bukhari"
            elif "مسلم" in attribution:
                source = "Sahih Muslim"
            elif "متفق عليه" in attribution:
                source = "Bukhari & Muslim"
            
            # Insérer dans la base
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO entries (
                    hadith_ar,
                    grade,
                    source,
                    explanation_ar,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                hadith_text,
                grade_normalized,
                source,
                explanation,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            self.stats['inserted'] += 1
            logger.info(f"✅ Hadith inséré: {source} ({grade_normalized})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur insert_hadith: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_category(
        self, 
        conn: sqlite3.Connection, 
        category: Dict,
        max_hadiths: Optional[int] = None
    ) -> int:
        """
        Harvest tous les hadiths d'une catégorie
        
        Returns:
            Nombre de hadiths insérés
        """
        category_id = int(category['id'])
        category_title = category['title']
        total_hadiths = int(category.get('hadeeths_count', 0))
        
        logger.info(f"\n📚 Catégorie: {category_title}")
        logger.info(f"   Total hadiths: {total_hadiths}")
        
        inserted_count = 0
        page = 1
        
        while True:
            # Vérifier la limite
            if max_hadiths and inserted_count >= max_hadiths:
                logger.info(f"⏸️  Limite atteinte: {max_hadiths} hadiths")
                break
            
            # Récupérer la page
            logger.info(f"   📄 Page {page}...")
            result = self.get_hadiths_by_category(category_id, page=page, per_page=50)
            
            if not result or 'data' not in result:
                break
            
            hadiths = result['data']
            if not hadiths:
                break
            
            # Traiter chaque hadith
            for hadith_summary in hadiths:
                hadith_id = int(hadith_summary['id'])
                
                # Récupérer les détails complets
                hadith_details = self.get_hadith_details(hadith_id)
                
                if hadith_details:
                    self.stats['total_processed'] += 1
                    
                    if self.insert_hadith(conn, hadith_details):
                        inserted_count += 1
                    
                    # Respecter les limites de l'API
                    time.sleep(0.1)
                
                # Vérifier la limite
                if max_hadiths and inserted_count >= max_hadiths:
                    break
            
            # Vérifier s'il y a d'autres pages
            meta = result.get('meta', {})
            if page >= meta.get('last_page', 1):
                break
            
            page += 1
            time.sleep(0.5)  # Pause entre les pages
        
        logger.info(f"✅ Catégorie terminée: {inserted_count} hadiths insérés")
        return inserted_count
    
    def harvest_all(self, max_hadiths_per_category: Optional[int] = None):
        """
        Harvest tous les hadiths de toutes les catégories
        
        Args:
            max_hadiths_per_category: Limite par catégorie (None = illimité)
        """
        logger.info("🕋 AL-MĪZĀN V7.0 — HARVESTING HADEETHENC")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Connexion à la base
        conn = sqlite3.connect(self.DB_PATH)
        
        try:
            # Récupérer les catégories
            categories = self.get_categories()
            
            if not categories:
                logger.error("❌ Aucune catégorie récupérée")
                return
            
            logger.info(f"\n📊 {len(categories)} catégories à traiter")
            
            # Traiter chaque catégorie
            for i, category in enumerate(categories, 1):
                logger.info(f"\n[{i}/{len(categories)}] Traitement...")
                self.harvest_category(conn, category, max_hadiths_per_category)
                
                # Pause entre les catégories
                time.sleep(1)
            
            # Statistiques finales
            elapsed = time.time() - start_time
            
            logger.info("\n" + "=" * 70)
            logger.info("📊 STATISTIQUES FINALES")
            logger.info("-" * 70)
            logger.info(f"Hadiths traités:     {self.stats['total_processed']}")
            logger.info(f"Hadiths insérés:     {self.stats['inserted']}")
            logger.info(f"Rejetés (grade):     {self.stats['skipped_grade']}")
            logger.info(f"Doublons:            {self.stats['skipped_duplicate']}")
            logger.info(f"Erreurs:             {self.stats['errors']}")
            logger.info(f"Temps écoulé:        {elapsed:.2f}s")
            logger.info("=" * 70)
            
        finally:
            conn.close()

def main():
    """Point d'entrée principal"""
    
    print("🕋 AL-MĪZĀN V7.0 — HARVESTER HADEETHENC")
    print("=" * 70)
    print("\nOptions:")
    print("1. Test (10 hadiths par catégorie)")
    print("2. Production (tous les hadiths)")
    print("3. Catégorie spécifique")
    
    choice = input("\nChoix (1-3): ").strip()
    
    harvester = HadeethEncHarvester()
    
    if choice == "1":
        print("\n🧪 MODE TEST: 10 hadiths par catégorie")
        harvester.harvest_all(max_hadiths_per_category=10)
    
    elif choice == "2":
        confirm = input("\n⚠️  MODE PRODUCTION: Extraire TOUS les hadiths ? (oui/non): ")
        if confirm.lower() == "oui":
            harvester.harvest_all()
        else:
            print("❌ Annulé")
    
    elif choice == "3":
        conn = sqlite3.connect(harvester.DB_PATH)
        try:
            categories = harvester.get_categories()
            print("\n📚 Catégories disponibles:")
            for i, cat in enumerate(categories[:10], 1):
                print(f"{i}. {cat['title']} ({cat['hadeeths_count']} hadiths)")
            
            cat_num = int(input("\nNuméro de catégorie: ")) - 1
            if 0 <= cat_num < len(categories):
                harvester.harvest_category(conn, categories[cat_num])
        finally:
            conn.close()
    
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main()