#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════
AL-MĪZĀN v7.0 — PRODUCTION HARVESTER
Compatible avec architecture v7 (table entries)
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
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = Path(__file__).parent / "database" / "almizan_v7.db"
LOG_FILE = Path(__file__).parent / "harvest_v7.log"
PROGRESS_FILE = Path(__file__).parent.parent / "output" / "HARVESTING_V7_STATUS.md"

# Configuration du logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8'
)

# API Dorar.net
DORAR_API = "https://dorar.net/dorar_api.json"

# Mapping des grades
GRADE_MAP = {
    "صحيح": ("Sahih", "SAHIH"),
    "حسن": ("Hasan", "HASAN"),
    "ضعيف": ("Daif", "DAIF"),
    "موضوع": ("Mawdū'", "MAWDUU"),
    "باطل": ("Batil", "BATIL"),
}

# ═══════════════════════════════════════════════════════════════════════════
# HARVESTER V7
# ═══════════════════════════════════════════════════════════════════════════

class HarvesterV7:
    """Harvester compatible avec architecture v7"""
    
    def __init__(self):
        self.stats = {
            'total_attempted': 0,
            'total_inserted': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def sha256_text(self, text: str) -> str:
        """Génère SHA256 d'un texte"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def parse_grade(self, grade_raw: str) -> Tuple[str, str]:
        """
        Parse le grade depuis l'API
        Retourne: (grade_primary, grade_category)
        """
        if not grade_raw:
            return ("Inconnu", "DAIF")
        
        grade_clean = grade_raw.strip()
        
        # Recherche exacte
        for key, (primary, category) in GRADE_MAP.items():
            if key in grade_clean:
                return (primary, category)
        
        # Par défaut
        logging.warning(f"GRADE_UNKNOWN | grade_raw={grade_raw}")
        return ("Inconnu", "DAIF")
    
    def validate_api_response(self, data) -> bool:
        """Valide que la réponse API est un dict valide"""
        if not isinstance(data, dict):
            logging.error(f"API_RESPONSE_NOT_DICT | type={type(data)}")
            return False
        return True
    
    def insert_hadith(self, conn: sqlite3.Connection, hadith_data: Dict) -> bool:
        """
        Insère un hadith dans la table entries (v7)
        """
        try:
            # Extraction des données
            matn_ar = hadith_data.get("hadith", "").strip()
            if not matn_ar:
                return False
            
            # Génération ID unique
            content_hash = self.sha256_text(matn_ar)
            entry_id = f"dorar_{content_hash[:12]}"
            
            # Parsing grade
            grade_raw = hadith_data.get("grade", "")
            grade_primary, _ = self.parse_grade(grade_raw)
            
            # Données du livre
            book_name_ar = hadith_data.get("book_name_ar", "")
            book_name_fr = hadith_data.get("book_name_fr", "")
            book_id_dorar = hadith_data.get("book_id_dorar", 0)
            
            # Traduction française
            matn_fr = hadith_data.get("translation_fr", "")
            
            # Insertion
            conn.execute("""
                INSERT OR IGNORE INTO entries (
                    id, zone_id, zone_label,
                    ar_text, ar_text_clean,
                    fr_text,
                    grade_primary, grade_by_mohdith,
                    book_name_ar, book_name_fr, book_id_dorar,
                    hadith_id_dorar,
                    source_api, source_url,
                    content_hash,
                    created_at, updated_at
                ) VALUES (
                    ?, 2, 'Matn',
                    ?, ?,
                    ?,
                    ?, ?,
                    ?, ?, ?,
                    ?,
                    'dorar.net', ?,
                    ?,
                    datetime('now'), datetime('now')
                )
            """, (
                entry_id,
                matn_ar, matn_ar,  # ar_text, ar_text_clean
                matn_fr,
                grade_primary, grade_raw,
                book_name_ar, book_name_fr, book_id_dorar,
                hadith_data.get("hadith_id", ""),
                hadith_data.get("url", ""),
                content_hash
            ))
            
            # Vérifier si insertion réussie
            if conn.total_changes > 0:
                self.stats['total_inserted'] += 1
                return True
            else:
                self.stats['total_duplicates'] += 1
                return False
                
        except Exception as e:
            self.stats['total_errors'] += 1
            logging.error(f"INSERT_ERROR | {e}")
            return False
    
    def harvest_book(self, book_key: str, book_config: Dict, max_hadiths: int = None) -> int:
        """
        Harveste un livre complet depuis Dorar
        """
        conn = sqlite3.connect(DB_PATH)
        
        book_name_ar = book_config["name_ar"]
        book_name_fr = book_config["name_fr"]
        book_id_dorar = book_config.get("dorar_id", 0)
        
        logging.info(f"DÉBUT LIVRE | {book_name_ar}")
        print(f"\n{'='*70}")
        print(f"📖 {book_name_ar}")
        print(f"   {book_name_fr}")
        print(f"{'='*70}")
        
        page = 1
        total_inserted = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            # Limite de sécurité
            if max_hadiths and total_inserted >= max_hadiths:
                print(f"\n✅ Limite atteinte: {max_hadiths} hadiths")
                break
            
            # Protection contre boucle infinie
            if consecutive_errors >= max_consecutive_errors:
                logging.error(f"ARRÊT | {book_name_ar} | trop d'erreurs")
                print(f"\n❌ Arrêt après {consecutive_errors} erreurs consécutives")
                break
            
            try:
                # Requête API
                print(f"\n🔄 Page {page}...", end=" ", flush=True)
                
                response = requests.get(
                    DORAR_API,
                    params={
                        "skey": book_name_ar,
                        "lang": "ar",
                        "page": page
                    },
                    timeout=15
                )
                
                if response.status_code != 200:
                    logging.error(f"API_ERROR | status={response.status_code}")
                    consecutive_errors += 1
                    time.sleep(3)
                    continue
                
                # Parser JSON
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logging.error(f"JSON_ERROR | {e}")
                    consecutive_errors += 1
                    time.sleep(3)
                    continue
                
                # Valider réponse
                if not self.validate_api_response(data):
                    consecutive_errors += 1
                    time.sleep(3)
                    continue
                
                # Extraire hadiths
                results = data.get("ahadith", [])
                
                # Si pas de résultats, fin du livre
                if not results or len(results) == 0:
                    print("✓ Fin")
                    logging.info(f"FIN LIVRE | {book_name_ar} | total={total_inserted}")
                    break
                
                # Reset compteur d'erreurs
                consecutive_errors = 0
                
                # Traiter chaque hadith
                batch_inserted = 0
                for h in results:
                    self.stats['total_attempted'] += 1
                    
                    # Enrichir avec métadonnées du livre
                    h["book_name_ar"] = book_name_ar
                    h["book_name_fr"] = book_name_fr
                    h["book_id_dorar"] = book_id_dorar
                    
                    if self.insert_hadith(conn, h):
                        batch_inserted += 1
                        total_inserted += 1
                
                conn.commit()
                print(f"✓ {batch_inserted} insérés")
                
                # Progress tous les 10 pages
                if page % 10 == 0:
                    print(f"\n📊 Progression: {total_inserted} hadiths insérés")
                
                # Rate limiting
                time.sleep(2.0)
                page += 1
                
            except Exception as e:
                logging.error(f"EXCEPTION | page={page} | {e}")
                consecutive_errors += 1
                time.sleep(3)
        
        conn.close()
        
        print(f"\n✅ {book_name_ar} TERMINÉ")
        print(f"   Total inséré: {total_inserted}")
        
        return total_inserted
    
    def print_stats(self):
        """Affiche les statistiques"""
        print(f"\n{'='*70}")
        print("📊 STATISTIQUES FINALES")
        print(f"{'='*70}")
        print(f"Tentatives:  {self.stats['total_attempted']}")
        print(f"Insérés:     {self.stats['total_inserted']}")
        print(f"Doublons:    {self.stats['total_duplicates']}")
        print(f"Erreurs:     {self.stats['total_errors']}")
        
        if self.stats['total_attempted'] > 0:
            success_rate = (self.stats['total_inserted'] / self.stats['total_attempted']) * 100
            print(f"Taux succès: {success_rate:.1f}%")

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION DES LIVRES
# ═══════════════════════════════════════════════════════════════════════════

BOOKS_CONFIG = {
    "bukhari": {
        "name_ar": "صحيح البخاري",
        "name_fr": "Sahih al-Bukhari",
        "dorar_id": 6216,
        "total_hadiths": 7563
    },
    "muslim": {
        "name_ar": "صحيح مسلم",
        "name_fr": "Sahih Muslim",
        "dorar_id": 3088,
        "total_hadiths": 7190
    },
    "abu_dawud": {
        "name_ar": "سنن أبي داود",
        "name_fr": "Sunan Abu Dawud",
        "dorar_id": 1666,
        "total_hadiths": 5274
    },
    "tirmidhi": {
        "name_ar": "جامع الترمذي",
        "name_fr": "Jami' at-Tirmidhi",
        "dorar_id": 1669,
        "total_hadiths": 3956
    },
    "nasai": {
        "name_ar": "سنن النسائي",
        "name_fr": "Sunan an-Nasa'i",
        "dorar_id": 1694,
        "total_hadiths": 5758
    },
    "ibn_majah": {
        "name_ar": "سنن ابن ماجه",
        "name_fr": "Sunan Ibn Majah",
        "dorar_id": 1670,
        "total_hadiths": 4341
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal"""
    print("\n" + "="*70)
    print("🕋 AL-MĪZĀN V7.0 — PRODUCTION HARVESTER")
    print("="*70)
    
    harvester = HarvesterV7()
    harvester.stats['start_time'] = datetime.now().isoformat()
    
    # Mode test: 50 hadiths de Bukhari
    print("\n⚠️  MODE TEST: 50 hadiths de Sahih al-Bukhari")
    
    harvester.harvest_book(
        book_key="bukhari",
        book_config=BOOKS_CONFIG["bukhari"],
        max_hadiths=50
    )
    
    harvester.stats['end_time'] = datetime.now().isoformat()
    harvester.print_stats()
    
    print(f"\n{'='*70}")
    print("✅ TEST TERMINÉ")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()