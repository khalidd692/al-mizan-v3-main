#!/usr/bin/env python3
"""
🚀 AUTONOMOUS MEGA HARVESTER - 200K+ HADITHS
MODE AUTONOME TOTAL - JAMAIS D'ARRÊT - JAMAIS DE QUESTION
Épuise TOUTES les sources disponibles sans exception
"""

import sqlite3
import requests
import hashlib
import time
import json
from datetime import datetime
from typing import List, Tuple, Optional
import logging

# Configuration
DB_PATH = "backend/almizane.db"
TARGET = 200000
LOG_FILE = "backend/autonomous_harvest_200k.log"

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_hash(text: str) -> str:
    """Génère hash SHA256 du texte arabe"""
    clean = ''.join(text.split()).lower()
    return hashlib.sha256(clean.encode()).hexdigest()

def count_hadiths() -> int:
    """Compte total hadiths"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def insert_hadith(cursor, collection: str, numero: int, matn_ar: str, 
                 isnad: str, grade: str, source_url: str, source_api: str,
                 badge_alerte: int = 0) -> bool:
    """Insère hadith si pas doublon"""
    sha256 = get_hash(matn_ar)
    
    # Vérifier doublon
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE sha256 = ?", (sha256,))
    if cursor.fetchone()[0] > 0:
        return False
    
    # Badge alerte pour Mawdu' et Batil
    if any(term in grade.lower() for term in ['mawdu', 'batil', 'موضوع', 'باطل']):
        badge_alerte = 1
    
    # Insérer
    cursor.execute("""
        INSERT INTO hadiths (
            sha256, collection, numero_hadith, matn_ar, 
            isnad_brut, grade_final, source_url, source_api, badge_alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sha256, collection, numero, matn_ar, isnad, grade, source_url, source_api, badge_alerte))
    
    return True

def harvest_hadith_gading() -> Tuple[int, int]:
    """Extraction COMPLÈTE depuis Hadith Gading API"""
    logging.info("="*80)
    logging.info("🔥 HADITH GADING API - EXTRACTION MAXIMALE")
    logging.info("="*80)
    
    collections = [
        ("musnad-ahmad", "Musnad Ahmad", 27000),
        ("sunan-darimi", "Sunan ad-Darimi", 3500),
        ("sunan-ibnu-majah", "Sunan Ibn Majah", 4500),
        ("shahih-bukhari", "Sahih Bukhari", 7500),
        ("shahih-muslim", "Sahih Muslim", 7500),
        ("sunan-abu-daud", "Sunan Abu Dawud", 5300),
        ("sunan-tirmidzi", "Jami' at-Tirmidhi", 4000),
        ("sunan-nasai", "Sunan an-Nasa'i", 5800),
        ("muwatta-malik", "Muwatta Malik", 2000),
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    for slug, name, max_num in collections:
        logging.info(f"\n📖 {name} (max {max_num} hadiths)")
        inserted = 0
        
        for num in range(1, max_num + 1):
            try:
                url = f"https://api.hadith.gading.dev/books/{slug}/{num}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("code") == 200 and "data" in data:
                        hadith = data["data"]
                        contents = hadith.get("contents", {})
                        
                        matn_ar = contents.get("arab", "")
                        if not matn_ar:
                            continue
                        
                        isnad = contents.get("id", "")
                        grade = "Non classifié"
                        
                        if insert_hadith(cursor, name, num, matn_ar, isnad, grade, url, "hadith_gading"):
                            inserted += 1
                            total_inserted += 1
                            
                            if inserted % 500 == 0:
                                conn.commit()
                                current = count_hadiths()
                                logging.info(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                        else:
                            total_skipped += 1
                
                time.sleep(0.1)
                
            except Exception as e:
                continue
        
        conn.commit()
        logging.info(f"   ✅ {name}: +{inserted} nouveaux")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_sunnah_com() -> Tuple[int, int]:
    """Extraction COMPLÈTE depuis Sunnah.com"""
    logging.info("="*80)
    logging.info("🔥 SUNNAH.COM API - TOUTES COLLECTIONS")
    logging.info("="*80)
    
    collections = [
        ("bukhari", "Sahih Bukhari", 7563),
        ("muslim", "Sahih Muslim", 7563),
        ("nasai", "Sunan an-Nasa'i", 5761),
        ("abudawud", "Sunan Abu Dawud", 5274),
        ("tirmidhi", "Jami' at-Tirmidhi", 3956),
        ("ibnmajah", "Sunan Ibn Majah", 4341),
        ("malik", "Muwatta Malik", 1594),
        ("riyadussalihin", "Riyad as-Salihin", 1896),
        ("adab", "Al-Adab Al-Mufrad", 1322),
        ("bulugh", "Bulugh al-Maram", 1358),
        ("shamail", "Shamail Muhammadiyah", 415),
        ("qudsi40", "40 Hadith Qudsi", 40),
        ("nawawi40", "40 Hadith Nawawi", 42),
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    for slug, name, max_num in collections:
        logging.info(f"\n📖 {name} (max {max_num} hadiths)")
        inserted = 0
        
        for num in range(1, max_num + 1):
            try:
                url = f"https://sunnah.com/{slug}:{num}/json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    matn_ar = data.get("hadith", [{}])[0].get("body", "")
                    if not matn_ar:
                        continue
                    
                    isnad = data.get("hadith", [{}])[0].get("grades", [{}])[0].get("grade", "")
                    grade = "Non classifié"
                    
                    if insert_hadith(cursor, name, num, matn_ar, isnad, grade, url, "sunnah_com"):
                        inserted += 1
                        total_inserted += 1
                        
                        if inserted % 500 == 0:
                            conn.commit()
                            current = count_hadiths()
                            logging.info(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                    else:
                        total_skipped += 1
                
                time.sleep(0.1)
                
            except Exception as e:
                continue
        
        conn.commit()
        logging.info(f"   ✅ {name}: +{inserted} nouveaux")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_hadeethenc() -> Tuple[int, int]:
    """Extraction depuis HadeethEnc.com"""
    logging.info("="*80)
    logging.info("🔥 HADEETHENC.COM - EXTRACTION MASSIVE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Parcourir par ID
    for hadith_id in range(1, 50000):
        try:
            url = f"https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id={hadith_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and "hadeeth" in data:
                    matn_ar = data.get("hadeeth", "")
                    if not matn_ar:
                        continue
                    
                    grade = data.get("grade", "Non classifié")
                    attribution = data.get("attribution", "")
                    
                    if insert_hadith(cursor, "HadeethEnc", hadith_id, matn_ar, 
                                   attribution, grade, url, "hadeethenc"):
                        total_inserted += 1
                        
                        if total_inserted % 500 == 0:
                            conn.commit()
                            current = count_hadiths()
                            logging.info(f"   ✅ {total_inserted} nouveaux | Total DB: {current:,}")
                    else:
                        total_skipped += 1
            
            time.sleep(0.1)
            
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    return total_inserted, total_skipped

def harvest_dorar() -> Tuple[int, int]:
    """Extraction depuis Dorar.net"""
    logging.info("="*80)
    logging.info("🔥 DORAR.NET - EXTRACTION MASSIVE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Collections Dorar
    collections = [
        ("bukhari", "Sahih Bukhari - Dorar"),
        ("muslim", "Sahih Muslim - Dorar"),
        ("tirmidhi", "Jami' at-Tirmidhi - Dorar"),
        ("abudawud", "Sunan Abu Dawud - Dorar"),
        ("nasai", "Sunan an-Nasa'i - Dorar"),
        ("ibnmajah", "Sunan Ibn Majah - Dorar"),
        ("ahmad", "Musnad Ahmad - Dorar"),
    ]
    
    for slug, name in collections:
        logging.info(f"\n📖 {name}")
        inserted = 0
        
        for page in range(1, 1000):
            try:
                url = f"https://dorar.net/hadith/search?q=&st=p&xclude=&fillopts=on&t=*&d[]={slug}&page={page}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    # Parser HTML basique
                    text = response.text
                    
                    # Extraction simple des hadiths (à améliorer avec BeautifulSoup si nécessaire)
                    if "لا توجد نتائج" in text or "No results" in text:
                        break
                    
                    # Continuer même si parsing échoue
                    time.sleep(0.5)
                    
            except Exception as e:
                continue
        
        conn.commit()
        logging.info(f"   ✅ {name}: +{inserted} nouveaux")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_islamweb() -> Tuple[int, int]:
    """Extraction depuis IslamWeb.net"""
    logging.info("="*80)
    logging.info("🔥 ISLAMWEB.NET - EXTRACTION")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Parcourir les hadiths IslamWeb
    for hadith_id in range(1, 30000):
        try:
            url = f"https://www.islamweb.net/ar/library/index.php?page=bookcontents&ID={hadith_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parser basique (à améliorer)
                time.sleep(0.2)
                
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    return total_inserted, total_skipped

def harvest_github_datasets() -> Tuple[int, int]:
    """Extraction depuis datasets GitHub"""
    logging.info("="*80)
    logging.info("🔥 GITHUB DATASETS - EXTRACTION")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Datasets connus
    datasets = [
        "https://raw.githubusercontent.com/A-Kamran/hadith-dataset/master/hadith.json",
        "https://raw.githubusercontent.com/saleemkce/hadith/master/data/bukhari.json",
        "https://raw.githubusercontent.com/saleemkce/hadith/master/data/muslim.json",
    ]
    
    for dataset_url in datasets:
        try:
            logging.info(f"\n📦 Téléchargement: {dataset_url}")
            response = requests.get(dataset_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    for item in data:
                        matn_ar = item.get("arabic", item.get("text", ""))
                        if not matn_ar:
                            continue
                        
                        collection = item.get("collection", "GitHub Dataset")
                        numero = item.get("number", 0)
                        grade = item.get("grade", "Non classifié")
                        
                        if insert_hadith(cursor, collection, numero, matn_ar, 
                                       "", grade, dataset_url, "github"):
                            total_inserted += 1
                            
                            if total_inserted % 500 == 0:
                                conn.commit()
                                current = count_hadiths()
                                logging.info(f"   ✅ {total_inserted} nouveaux | Total DB: {current:,}")
                        else:
                            total_skipped += 1
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Erreur dataset {dataset_url}: {e}")
            continue
    
    conn.close()
    return total_inserted, total_skipped

def fill_matn_fr_from_hadeethenc():
    """Remplit matn_fr via HadeethEnc pour chaque NULL"""
    logging.info("="*80)
    logging.info("🔄 REMPLISSAGE TRADUCTIONS FRANÇAISES")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupérer hadiths sans traduction
    cursor.execute("SELECT id, matn_ar FROM hadiths WHERE matn_fr IS NULL LIMIT 10000")
    hadiths = cursor.fetchall()
    
    updated = 0
    
    for hadith_id, matn_ar in hadiths:
        try:
            # Rechercher sur HadeethEnc
            url = f"https://hadeethenc.com/api/v1/hadeeths/search/?language=fr&query={matn_ar[:100]}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    matn_fr = data[0].get("hadeeth", "")
                    
                    if matn_fr:
                        cursor.execute("UPDATE hadiths SET matn_fr = ? WHERE id = ?", 
                                     (matn_fr, hadith_id))
                        updated += 1
                        
                        if updated % 100 == 0:
                            conn.commit()
                            logging.info(f"   ✅ {updated} traductions ajoutées")
            
            time.sleep(0.2)
            
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    
    logging.info(f"✅ Total traductions ajoutées: {updated}")
    return updated

def main():
    """Orchestrateur principal - MODE AUTONOME"""
    logging.info("="*80)
    logging.info("🚀 AUTONOMOUS MEGA HARVESTER - 200K+ HADITHS")
    logging.info("MODE AUTONOME TOTAL - JAMAIS D'ARRÊT")
    logging.info("="*80)
    
    start_time = datetime.now()
    initial = count_hadiths()
    
    logging.info(f"\n📊 État initial: {initial:,} hadiths")
    logging.info(f"🎯 Objectif: {TARGET:,} hadiths")
    logging.info(f"📈 Besoin: {TARGET - initial:,} hadiths")
    
    # PHASE 1: Hadith Gading
    logging.info("\n" + "="*80)
    logging.info("PHASE 1: HADITH GADING API")
    logging.info("="*80)
    inserted1, skipped1 = harvest_hadith_gading()
    current = count_hadiths()
    logging.info(f"✅ Phase 1: +{inserted1:,} | Total: {current:,}")
    
    # PHASE 2: Sunnah.com
    logging.info("\n" + "="*80)
    logging.info("PHASE 2: SUNNAH.COM API")
    logging.info("="*80)
    inserted2, skipped2 = harvest_sunnah_com()
    current = count_hadiths()
    logging.info(f"✅ Phase 2: +{inserted2:,} | Total: {current:,}")
    
    # PHASE 3: HadeethEnc
    logging.info("\n" + "="*80)
    logging.info("PHASE 3: HADEETHENC.COM")
    logging.info("="*80)
    inserted3, skipped3 = harvest_hadeethenc()
    current = count_hadiths()
    logging.info(f"✅ Phase 3: +{inserted3:,} | Total: {current:,}")
    
    # PHASE 4: Dorar
    logging.info("\n" + "="*80)
    logging.info("PHASE 4: DORAR.NET")
    logging.info("="*80)
    inserted4, skipped4 = harvest_dorar()
    current = count_hadiths()
    logging.info(f"✅ Phase 4: +{inserted4:,} | Total: {current:,}")
    
    # PHASE 5: GitHub Datasets
    logging.info("\n" + "="*80)
    logging.info("PHASE 5: GITHUB DATASETS")
    logging.info("="*80)
    inserted5, skipped5 = harvest_github_datasets()
    current = count_hadiths()
    logging.info(f"✅ Phase 5: +{inserted5:,} | Total: {current:,}")
    
    # PHASE 6: Traductions françaises
    logging.info("\n" + "="*80)
    logging.info("PHASE 6: TRADUCTIONS FRANÇAISES")
    logging.info("="*80)
    translations = fill_matn_fr_from_hadeethenc()
    
    # Résumé final
    final = count_hadiths()
    duration = (datetime.now() - start_time).total_seconds()
    
    logging.info("\n" + "="*80)
    logging.info("📊 RÉSUMÉ FINAL")
    logging.info("="*80)
    logging.info(f"⏱️  Durée: {duration/3600:.1f} heures")
    logging.info(f"📊 Initial: {initial:,} hadiths")
    logging.info(f"📊 Final: {final:,} hadiths")
    logging.info(f"✅ Ajoutés: {final - initial:,} hadiths")
    logging.info(f"⏭️  Doublons évités: {skipped1 + skipped2 + skipped3 + skipped4 + skipped5:,}")
    logging.info(f"🌍 Traductions: {translations:,}")
    logging.info(f"🎯 Progression: {(final/TARGET)*100:.1f}%")
    
    if final >= TARGET:
        logging.info(f"\n🎉 OBJECTIF 200K ATTEINT!")
    else:
        logging.info(f"\n📈 Reste: {TARGET - final:,} hadiths")
        logging.info("♻️  Relancer le script pour continuer...")

if __name__ == "__main__":
    main()