#!/usr/bin/env python3
"""
🚀 ULTIMATE AUTONOMOUS HARVESTER - 200K+ HADITHS
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
from bs4 import BeautifulSoup
import re

# Configuration
DB_PATH = "backend/almizane.db"
TARGET = 200000
LOG_FILE = "backend/ultimate_harvest.log"

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
                 badge_alerte: int = 0, matn_fr: str = "") -> bool:
    """Insère hadith si pas doublon"""
    if not matn_ar or len(matn_ar) < 10:
        return False
        
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
            sha256, collection, numero_hadith, matn_ar, matn_fr,
            isnad_brut, grade_final, source_url, source_api, badge_alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sha256, collection, numero, matn_ar, matn_fr, isnad, grade, source_url, source_api, badge_alerte))
    
    return True

def harvest_hadith_gading_complete() -> Tuple[int, int]:
    """Extraction COMPLÈTE depuis Hadith Gading API"""
    logging.info("="*80)
    logging.info("🔥 HADITH GADING API - EXTRACTION MAXIMALE")
    logging.info("="*80)
    
    collections = [
        ("musnad-ahmad", "Musnad Ahmad", 27000),
        ("sunan-darimi", "Sunan ad-Darimi", 3500),
        ("sunan-ibnu-majah", "Sunan Ibn Majah", 4500),
        ("shahih-bukhari", "Sahih Bukhari", 7600),
        ("shahih-muslim", "Sahih Muslim", 7600),
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
                
                time.sleep(0.05)
                
            except Exception as e:
                continue
        
        conn.commit()
        logging.info(f"   ✅ {name}: +{inserted} nouveaux")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_sunnah_com_complete() -> Tuple[int, int]:
    """Extraction COMPLÈTE depuis Sunnah.com"""
    logging.info("="*80)
    logging.info("🔥 SUNNAH.COM API - TOUTES COLLECTIONS")
    logging.info("="*80)
    
    collections = [
        ("bukhari", "Sahih Bukhari - Sunnah", 7563),
        ("muslim", "Sahih Muslim - Sunnah", 7563),
        ("nasai", "Sunan an-Nasa'i - Sunnah", 5761),
        ("abudawud", "Sunan Abu Dawud - Sunnah", 5274),
        ("tirmidhi", "Jami' at-Tirmidhi - Sunnah", 3956),
        ("ibnmajah", "Sunan Ibn Majah - Sunnah", 4341),
        ("malik", "Muwatta Malik - Sunnah", 1594),
        ("riyadussalihin", "Riyad as-Salihin", 1896),
        ("adab", "Al-Adab Al-Mufrad", 1322),
        ("bulugh", "Bulugh al-Maram", 1358),
        ("shamail", "Shamail Muhammadiyah", 415),
        ("qudsi40", "40 Hadith Qudsi", 40),
        ("nawawi40", "40 Hadith Nawawi - Sunnah", 42),
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
                url = f"https://sunnah.com/{slug}:{num}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraire texte arabe
                    arabic_div = soup.find('div', class_='arabic_hadith_full')
                    if arabic_div:
                        matn_ar = arabic_div.get_text(strip=True)
                        
                        # Extraire grade
                        grade_div = soup.find('td', class_='english_grade')
                        grade = grade_div.get_text(strip=True) if grade_div else "Non classifié"
                        
                        if insert_hadith(cursor, name, num, matn_ar, "", grade, url, "sunnah_com"):
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

def harvest_hadeethenc_massive() -> Tuple[int, int]:
    """Extraction MASSIVE depuis HadeethEnc.com"""
    logging.info("="*80)
    logging.info("🔥 HADEETHENC.COM - EXTRACTION MASSIVE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Parcourir par ID jusqu'à 100,000
    for hadith_id in range(1, 100000):
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
                    
                    # Récupérer traduction française
                    matn_fr = ""
                    try:
                        url_fr = f"https://hadeethenc.com/api/v1/hadeeths/one/?language=fr&id={hadith_id}"
                        response_fr = requests.get(url_fr, timeout=10)
                        if response_fr.status_code == 200:
                            data_fr = response_fr.json()
                            matn_fr = data_fr.get("hadeeth", "")
                    except:
                        pass
                    
                    if insert_hadith(cursor, "HadeethEnc", hadith_id, matn_ar, 
                                   attribution, grade, url, "hadeethenc", 0, matn_fr):
                        total_inserted += 1
                        
                        if total_inserted % 500 == 0:
                            conn.commit()
                            current = count_hadiths()
                            logging.info(f"   ✅ {total_inserted} nouveaux | Total DB: {current:,}")
                    else:
                        total_skipped += 1
            
            time.sleep(0.05)
            
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    return total_inserted, total_skipped

def harvest_dorar_massive() -> Tuple[int, int]:
    """Extraction MASSIVE depuis Dorar.net"""
    logging.info("="*80)
    logging.info("🔥 DORAR.NET - EXTRACTION MASSIVE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Collections Dorar
    collections = [
        ("1", "Sahih Bukhari - Dorar"),
        ("2", "Sahih Muslim - Dorar"),
        ("3", "Jami' at-Tirmidhi - Dorar"),
        ("4", "Sunan Abu Dawud - Dorar"),
        ("5", "Sunan an-Nasa'i - Dorar"),
        ("6", "Sunan Ibn Majah - Dorar"),
        ("7", "Musnad Ahmad - Dorar"),
        ("8", "Muwatta Malik - Dorar"),
        ("9", "Sunan ad-Darimi - Dorar"),
    ]
    
    for coll_id, name in collections:
        logging.info(f"\n📖 {name}")
        inserted = 0
        
        for page in range(1, 2000):
            try:
                url = f"https://dorar.net/hadith/search?q=&st=p&xclude=&fillopts=on&t=*&d[]={coll_id}&page={page}"
                response = requests.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extraire hadiths
                    hadith_divs = soup.find_all('div', class_='hadith')
                    
                    if not hadith_divs:
                        break
                    
                    for hadith_div in hadith_divs:
                        try:
                            # Extraire texte arabe
                            matn_div = hadith_div.find('div', class_='hadith_text')
                            if matn_div:
                                matn_ar = matn_div.get_text(strip=True)
                                
                                # Extraire grade
                                grade_div = hadith_div.find('div', class_='grade')
                                grade = grade_div.get_text(strip=True) if grade_div else "Non classifié"
                                
                                # Extraire numéro
                                num_match = re.search(r'رقم\s*(\d+)', hadith_div.get_text())
                                numero = int(num_match.group(1)) if num_match else 0
                                
                                if insert_hadith(cursor, name, numero, matn_ar, "", grade, url, "dorar"):
                                    inserted += 1
                                    total_inserted += 1
                                    
                                    if inserted % 100 == 0:
                                        conn.commit()
                                        current = count_hadiths()
                                        logging.info(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                                else:
                                    total_skipped += 1
                        except:
                            continue
                    
                    time.sleep(0.5)
                else:
                    break
                    
            except Exception as e:
                continue
        
        conn.commit()
        logging.info(f"   ✅ {name}: +{inserted} nouveaux")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_github_datasets_complete() -> Tuple[int, int]:
    """Extraction COMPLÈTE depuis datasets GitHub"""
    logging.info("="*80)
    logging.info("🔥 GITHUB DATASETS - EXTRACTION COMPLÈTE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Datasets connus
    datasets = [
        ("https://raw.githubusercontent.com/A-Kamran/hadith-dataset/master/hadith.json", "GitHub-Kamran"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/bukhari.json", "GitHub-Bukhari"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/muslim.json", "GitHub-Muslim"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/abudawud.json", "GitHub-AbuDawud"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/tirmidhi.json", "GitHub-Tirmidhi"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/nasai.json", "GitHub-Nasai"),
        ("https://raw.githubusercontent.com/saleemkce/hadith/master/data/ibnmajah.json", "GitHub-IbnMajah"),
    ]
    
    for dataset_url, source_name in datasets:
        try:
            logging.info(f"\n📦 {source_name}")
            response = requests.get(dataset_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                inserted = 0
                
                if isinstance(data, list):
                    for item in data:
                        matn_ar = item.get("arabic", item.get("text", item.get("hadith", "")))
                        if not matn_ar:
                            continue
                        
                        collection = item.get("collection", source_name)
                        numero = item.get("number", item.get("hadithNumber", 0))
                        grade = item.get("grade", "Non classifié")
                        
                        if insert_hadith(cursor, collection, numero, matn_ar, 
                                       "", grade, dataset_url, "github"):
                            inserted += 1
                            total_inserted += 1
                            
                            if inserted % 500 == 0:
                                conn.commit()
                                current = count_hadiths()
                                logging.info(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                        else:
                            total_skipped += 1
                
                conn.commit()
                logging.info(f"   ✅ {source_name}: +{inserted} nouveaux")
                
        except Exception as e:
            logging.error(f"Erreur {source_name}: {e}")
            continue
    
    conn.close()
    return total_inserted, total_skipped

def harvest_islamweb_massive() -> Tuple[int, int]:
    """Extraction MASSIVE depuis IslamWeb.net"""
    logging.info("="*80)
    logging.info("🔥 ISLAMWEB.NET - EXTRACTION MASSIVE")
    logging.info("="*80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    # Parcourir les hadiths IslamWeb
    for hadith_id in range(1, 50000):
        try:
            url = f"https://www.islamweb.net/ar/library/index.php?page=bookcontents&idfrom=1&idto=1&bk_no=0&ID={hadith_id}"
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extraire texte arabe
                content_div = soup.find('div', class_='hadith_text')
                if content_div:
                    matn_ar = content_div.get_text(strip=True)
                    
                    if insert_hadith(cursor, "IslamWeb", hadith_id, matn_ar, "", "Non classifié", url, "islamweb"):
                        total_inserted += 1
                        
                        if total_inserted % 500 == 0:
                            conn.commit()
                            current = count_hadiths()
                            logging.info(f"   ✅ {total_inserted} nouveaux | Total DB: {current:,}")
                    else:
                        total_skipped += 1
                
                time.sleep(0.2)
                
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    return total_inserted, total_skipped

def main():
    """Orchestrateur principal - MODE AUTONOME TOTAL"""
    logging.info("="*80)
    logging.info("🚀 ULTIMATE AUTONOMOUS HARVESTER - 200K+ HADITHS")
    logging.info("MODE AUTONOME TOTAL - JAMAIS D'ARRÊT")
    logging.info("="*80)
    
    start_time = datetime.now()
    initial = count_hadiths()
    
    logging.info(f"\n📊 État initial: {initial:,} hadiths")
    logging.info(f"🎯 Objectif: {TARGET:,} hadiths")
    logging.info(f"📈 Besoin: {TARGET - initial:,} hadiths")
    
    # PHASE 1: Hadith Gading COMPLET
    logging.info("\n" + "="*80)
    logging.info("PHASE 1: HADITH GADING API - EXTRACTION COMPLÈTE")
    logging.info("="*80)
    inserted1, skipped1 = harvest_hadith_gading_complete()
    current = count_hadiths()
    logging.info(f"✅ Phase 1: +{inserted1:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
    # PHASE 2: Sunnah.com COMPLET
    logging.info("\n" + "="*80)
    logging.info("PHASE 2: SUNNAH.COM API - EXTRACTION COMPLÈTE")
    logging.info("="*80)
    inserted2, skipped2 = harvest_sunnah_com_complete()
    current = count_hadiths()
    logging.info(f"✅ Phase 2: +{inserted2:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
    # PHASE 3: HadeethEnc MASSIF
    logging.info("\n" + "="*80)
    logging.info("PHASE 3: HADEETHENC.COM - EXTRACTION MASSIVE")
    logging.info("="*80)
    inserted3, skipped3 = harvest_hadeethenc_massive()
    current = count_hadiths()
    logging.info(f"✅ Phase 3: +{inserted3:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
    # PHASE 4: Dorar MASSIF
    logging.info("\n" + "="*80)
    logging.info("PHASE 4: DORAR.NET - EXTRACTION MASSIVE")
    logging.info("="*80)
    inserted4, skipped4 = harvest_dorar_massive()
    current = count_hadiths()
    logging.info(f"✅ Phase 4: +{inserted4:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
    # PHASE 5: GitHub Datasets COMPLET
    logging.info("\n" + "="*80)
    logging.info("PHASE 5: GITHUB DATASETS - EXTRACTION COMPLÈTE")
    logging.info("="*80)
    inserted5, skipped5 = harvest_github_datasets_complete()
    current = count_hadiths()
    logging.info(f"✅ Phase 5: +{inserted5:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
    # PHASE 6: IslamWeb MASSIF
    logging.info("\n" + "="*80)
    logging.info("PHASE 6: ISLAMWEB.NET - EXTRACTION MASSIVE")
    logging.info("="*80)
    inserted6, skipped6 = harvest_islamweb_massive()
    current = count_hadiths()
    logging.info(f"✅ Phase 6: +{inserted6:,} | Total: {current:,} | Progression: {(current/TARGET)*100:.1f}%")
    
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
    logging.info(f"⏭️  Doublons évités: {skipped1 + skipped2 + skipped3 + skipped4 + skipped5 + skipped6:,}")
    logging.info(f"🎯 Progression: {(final/TARGET)*100:.1f}%")
    
    if final >= TARGET:
        logging.info(f"\n🎉 OBJECTIF 200K ATTEINT!")
    else:
        logging.info(f"\n📈 Reste: {TARGET - final:,} hadiths")
        logging.info("♻️  Relancer le script pour continuer...")

if __name__ == "__main__":
    main()