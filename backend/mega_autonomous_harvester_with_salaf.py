#!/usr/bin/env python3
"""
MEGA AUTONOMOUS HARVESTER - 200K+ HADITHS
Inclut TOUTES les sources + Sites Salafies
Mode autonome total - Jamais d'arrêt
"""

import sqlite3
import requests
import hashlib
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
import json

# Configuration
DB_PATH = "backend/almizane.db"
LOG_FILE = "backend/mega_harvest_with_salaf.log"
TARGET = 200000

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_hash(text):
    """Génère hash SHA256"""
    if not text:
        return None
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def hash_exists(cursor, hash_val):
    """Vérifie si hash existe"""
    if not hash_val:
        return False
    cursor.execute("SELECT 1 FROM hadiths WHERE matn_ar_hash = ? LIMIT 1", (hash_val,))
    return cursor.fetchone() is not None

def detect_badge_alerte(grade, matn_ar):
    """Détecte si hadith est Mawdu' ou Batil"""
    if not grade and not matn_ar:
        return 0
    
    text = f"{grade or ''} {matn_ar or ''}".lower()
    
    mawdu_patterns = ['موضوع', 'mawdu', 'fabricated', 'forgery']
    batil_patterns = ['باطل', 'batil', 'false', 'invalid']
    
    for pattern in mawdu_patterns + batil_patterns:
        if pattern in text:
            return 1
    
    return 0

def insert_hadith(cursor, data):
    """Insère hadith avec vérification doublon"""
    hash_val = get_hash(data.get('matn_ar'))
    
    if hash_exists(cursor, hash_val):
        return False
    
    badge = detect_badge_alerte(data.get('grade_final'), data.get('matn_ar'))
    
    cursor.execute("""
        INSERT INTO hadiths (
            collection, book, chapter, hadith_number,
            matn_ar, matn_fr, isnad, grade_final,
            source_api, source_url, metadata_json,
            matn_ar_hash, badge_alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('collection'),
        data.get('book'),
        data.get('chapter'),
        data.get('hadith_number'),
        data.get('matn_ar'),
        data.get('matn_fr'),
        data.get('isnad'),
        data.get('grade_final'),
        data.get('source_api'),
        data.get('source_url'),
        data.get('metadata_json'),
        hash_val,
        badge
    ))
    
    return True

# ============================================================================
# PHASE 1: HADITH GADING API
# ============================================================================

def harvest_hadith_gading():
    """Phase 1: Hadith Gading API - Extraction complète"""
    logging.info("=" * 80)
    logging.info("PHASE 1: HADITH GADING API")
    logging.info("=" * 80)
    
    collections = [
        ("ahmad", 27000),
        ("bukhari", 7600),
        ("muslim", 7600),
        ("abudawud", 5300),
        ("tirmidzi", 4000),
        ("nasai", 5800),
        ("ibnmajah", 4500),
        ("darimi", 3500),
        ("malik", 2000)
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for slug, max_num in collections:
        logging.info(f"\nCollection: {slug} (max {max_num})")
        
        for num in range(1, max_num + 1):
            try:
                url = f"https://hadith-api-id.vercel.app/hadith/{slug}/{num}"
                resp = requests.get(url, headers=HEADERS, timeout=10)
                
                if resp.status_code == 200:
                    data_json = resp.json()
                    
                    hadith_data = {
                        'collection': slug,
                        'hadith_number': str(num),
                        'matn_ar': data_json.get('arabic'),
                        'matn_fr': None,
                        'grade_final': data_json.get('grade'),
                        'source_api': 'hadith_gading',
                        'source_url': url,
                        'metadata_json': json.dumps(data_json)
                    }
                    
                    if insert_hadith(cursor, hadith_data):
                        inserted += 1
                        if inserted % 500 == 0:
                            conn.commit()
                            logging.info(f"  {slug}: {inserted} insérés, {skipped} doublons")
                    else:
                        skipped += 1
                
                time.sleep(0.05)
                
            except Exception as e:
                logging.error(f"Erreur {slug} #{num}: {e}")
                continue
    
    conn.commit()
    conn.close()
    
    logging.info(f"\nPhase 1 terminée: +{inserted} hadiths")
    return inserted, skipped

# ============================================================================
# PHASE 2: HADEETHENC API
# ============================================================================

def harvest_hadeethenc():
    """Phase 2: HadeethEnc - Scan massif avec traductions FR"""
    logging.info("=" * 80)
    logging.info("PHASE 2: HADEETHENC API")
    logging.info("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for hadith_id in range(1, 100001):
        try:
            url = f"https://hadeethenc.com/api/v1/hadeeths/one/?language=fr&id={hadith_id}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                
                hadith_data = {
                    'collection': data.get('book', {}).get('title', 'HadeethEnc'),
                    'hadith_number': str(hadith_id),
                    'matn_ar': data.get('hadeeth'),
                    'matn_fr': data.get('translated_hadeeth'),
                    'grade_final': data.get('grade'),
                    'source_api': 'hadeethenc',
                    'source_url': url,
                    'metadata_json': json.dumps(data)
                }
                
                if insert_hadith(cursor, hadith_data):
                    inserted += 1
                    if inserted % 500 == 0:
                        conn.commit()
                        logging.info(f"  HadeethEnc: {inserted} insérés, {skipped} doublons")
                else:
                    skipped += 1
            
            time.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Erreur HadeethEnc #{hadith_id}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    logging.info(f"\nPhase 2 terminée: +{inserted} hadiths")
    return inserted, skipped

# ============================================================================
# PHASE 3: DORAR.NET SCRAPING
# ============================================================================

def harvest_dorar():
    """Phase 3: Dorar.net - Scraping HTML"""
    logging.info("=" * 80)
    logging.info("PHASE 3: DORAR.NET SCRAPING")
    logging.info("=" * 80)
    
    collections = [
        ("البخاري", 1, 8000),
        ("مسلم", 1, 8000),
        ("الترمذي", 1, 4000),
        ("أبو داود", 1, 5500),
        ("النسائي", 1, 6000),
        ("ابن ماجه", 1, 4500),
        ("أحمد", 1, 28000),
        ("مالك", 1, 2000),
        ("الدارمي", 1, 3500)
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for collection_ar, start, end in collections:
        logging.info(f"\nDorar: {collection_ar}")
        
        for num in range(start, end + 1):
            try:
                url = f"https://dorar.net/hadith/search?q={collection_ar}+{num}"
                resp = requests.get(url, headers=HEADERS, timeout=10)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    hadith_divs = soup.find_all('div', class_='hadith')
                    
                    for div in hadith_divs:
                        matn = div.find('div', class_='matn')
                        grade = div.find('div', class_='grade')
                        
                        if matn:
                            hadith_data = {
                                'collection': f"{collection_ar} - Dorar",
                                'hadith_number': str(num),
                                'matn_ar': matn.get_text(strip=True),
                                'grade_final': grade.get_text(strip=True) if grade else None,
                                'source_api': 'dorar_net',
                                'source_url': url
                            }
                            
                            if insert_hadith(cursor, hadith_data):
                                inserted += 1
                                if inserted % 500 == 0:
                                    conn.commit()
                                    logging.info(f"  Dorar: {inserted} insérés")
                            else:
                                skipped += 1
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"Erreur Dorar {collection_ar} #{num}: {e}")
                continue
    
    conn.commit()
    conn.close()
    
    logging.info(f"\nPhase 3 terminée: +{inserted} hadiths")
    return inserted, skipped

# ============================================================================
# PHASE 4: SITES SAVANTS SALAF
# ============================================================================

def harvest_binbaz():
    """Harvest hadiths depuis binbaz.org.sa"""
    logging.info("\nSite: binbaz.org.sa")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    try:
        # Scraping des fatwas contenant des hadiths
        for page in range(1, 500):
            url = f"https://binbaz.org.sa/fatwas?page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Extraire hadiths des fatwas
                hadith_blocks = soup.find_all(text=re.compile(r'(قال رسول الله|عن النبي|روى)'))
                
                for block in hadith_blocks:
                    parent = block.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        
                        if len(text) > 50 and len(text) < 2000:
                            hadith_data = {
                                'collection': 'Bin Baz - Fatwas',
                                'matn_ar': text,
                                'source_api': 'binbaz_org',
                                'source_url': url
                            }
                            
                            if insert_hadith(cursor, hadith_data):
                                inserted += 1
                                if inserted % 100 == 0:
                                    conn.commit()
                                    logging.info(f"    Bin Baz: {inserted} hadiths")
                            else:
                                skipped += 1
            
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Erreur Bin Baz: {e}")
    
    conn.commit()
    conn.close()
    
    return inserted, skipped

def harvest_ibnothaimeen():
    """Harvest hadiths depuis ibnothaimeen.com"""
    logging.info("\nSite: ibnothaimeen.com")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    try:
        for page in range(1, 300):
            url = f"https://ibnothaimeen.com/all/books/index.shtml?page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                hadith_blocks = soup.find_all(text=re.compile(r'(حديث|الحديث|رواه)'))
                
                for block in hadith_blocks:
                    parent = block.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        
                        if len(text) > 50 and len(text) < 2000:
                            hadith_data = {
                                'collection': 'Ibn Uthaymin - Livres',
                                'matn_ar': text,
                                'source_api': 'ibnothaimeen_com',
                                'source_url': url
                            }
                            
                            if insert_hadith(cursor, hadith_data):
                                inserted += 1
                                if inserted % 100 == 0:
                                    conn.commit()
                                    logging.info(f"    Ibn Uthaymin: {inserted} hadiths")
                            else:
                                skipped += 1
            
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Erreur Ibn Uthaymin: {e}")
    
    conn.commit()
    conn.close()
    
    return inserted, skipped

def harvest_islamqa():
    """Harvest hadiths depuis islamqa.info"""
    logging.info("\nSite: islamqa.info")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    try:
        for question_id in range(1, 100000):
            url = f"https://islamqa.info/ar/answers/{question_id}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Chercher les hadiths dans la réponse
                answer_div = soup.find('div', class_='answer-text')
                
                if answer_div:
                    hadith_blocks = answer_div.find_all(text=re.compile(r'(قال النبي|عن رسول الله|رواه البخاري|رواه مسلم)'))
                    
                    for block in hadith_blocks:
                        parent = block.parent
                        if parent:
                            text = parent.get_text(strip=True)
                            
                            if len(text) > 50 and len(text) < 2000:
                                hadith_data = {
                                    'collection': 'IslamQA - Fatwas',
                                    'matn_ar': text,
                                    'source_api': 'islamqa_info',
                                    'source_url': url
                                }
                                
                                if insert_hadith(cursor, hadith_data):
                                    inserted += 1
                                    if inserted % 100 == 0:
                                        conn.commit()
                                        logging.info(f"    IslamQA: {inserted} hadiths")
                                else:
                                    skipped += 1
            
            time.sleep(0.5)
            
            if question_id % 1000 == 0:
                logging.info(f"    IslamQA: Question {question_id}/100000")
            
    except Exception as e:
        logging.error(f"Erreur IslamQA: {e}")
    
    conn.commit()
    conn.close()
    
    return inserted, skipped

def harvest_sites_salaf():
    """Phase 4: Sites savants salafies"""
    logging.info("=" * 80)
    logging.info("PHASE 4: SITES SAVANTS SALAF")
    logging.info("=" * 80)
    
    total_inserted = 0
    total_skipped = 0
    
    # Bin Baz
    ins, skip = harvest_binbaz()
    total_inserted += ins
    total_skipped += skip
    
    # Ibn Uthaymin
    ins, skip = harvest_ibnothaimeen()
    total_inserted += ins
    total_skipped += skip
    
    # IslamQA
    ins, skip = harvest_islamqa()
    total_inserted += ins
    total_skipped += skip
    
    logging.info(f"\nPhase 4 terminée: +{total_inserted} hadiths")
    return total_inserted, total_skipped

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Orchestrateur principal"""
    logging.info("=" * 80)
    logging.info("MEGA AUTONOMOUS HARVESTER - 200K+ HADITHS")
    logging.info("INCLUT SOURCES SALAFIES")
    logging.info("MODE AUTONOME TOTAL - JAMAIS D'ARRET")
    logging.info("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    initial = cursor.fetchone()[0]
    conn.close()
    
    logging.info(f"\nEtat initial: {initial:,} hadiths")
    logging.info(f"Objectif: {TARGET:,} hadiths")
    logging.info(f"Besoin: {TARGET - initial:,} hadiths")
    
    logging.info("\n" + "=" * 80)
    
    # Phase 1: Hadith Gading
    ins1, skip1 = harvest_hadith_gading()
    
    # Phase 2: HadeethEnc
    ins2, skip2 = harvest_hadeethenc()
    
    # Phase 3: Dorar
    ins3, skip3 = harvest_dorar()
    
    # Phase 4: Sites Salaf
    ins4, skip4 = harvest_sites_salaf()
    
    # Rapport final
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    final = cursor.fetchone()[0]
    conn.close()
    
    total_inserted = ins1 + ins2 + ins3 + ins4
    
    logging.info("\n" + "=" * 80)
    logging.info("RAPPORT FINAL")
    logging.info("=" * 80)
    logging.info(f"Initial:        {initial:,} hadiths")
    logging.info(f"Final:          {final:,} hadiths")
    logging.info(f"Ajoutes:        +{total_inserted:,} hadiths")
    logging.info(f"Progression:    {(final/TARGET)*100:.1f}%")
    logging.info("=" * 80)

if __name__ == "__main__":
    main()