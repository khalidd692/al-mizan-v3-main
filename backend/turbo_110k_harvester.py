#!/usr/bin/env python3
"""
🚀 TURBO HARVESTER - Extraction rapide vers 110K
Cible toutes les sources disponibles sans doublons
"""

import sqlite3
import requests
import hashlib
import time
from datetime import datetime

DB_PATH = "backend/almizane.db"
TARGET = 110000

def get_hash(text):
    """Génère hash SHA256 du texte arabe"""
    clean = ''.join(text.split()).lower()
    return hashlib.sha256(clean.encode()).hexdigest()

def count_hadiths():
    """Compte total hadiths"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def insert_hadith(cursor, collection, numero, matn_ar, isnad, grade, source_url, source_api):
    """Insère hadith si pas doublon"""
    sha256 = get_hash(matn_ar)
    
    # Vérifier doublon
    cursor.execute("SELECT COUNT(*) FROM hadiths WHERE sha256 = ?", (sha256,))
    if cursor.fetchone()[0] > 0:
        return False
    
    # Insérer
    cursor.execute("""
        INSERT INTO hadiths (
            sha256, collection, numero_hadith, matn_ar, 
            isnad_brut, grade_final, source_url, source_api
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (sha256, collection, numero, matn_ar, isnad, grade, source_url, source_api))
    
    return True

def harvest_hadith_gading():
    """Extraction depuis Hadith Gading API"""
    print("\n🔥 HADITH GADING API - Extraction maximale")
    
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
        print(f"\n📖 {name} (max {max_num} hadiths)")
        inserted = 0
        skipped = 0
        
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
                        source_url = url
                        
                        if insert_hadith(cursor, name, num, matn_ar, isnad, grade, source_url, "hadith_gading"):
                            inserted += 1
                            total_inserted += 1
                            
                            if inserted % 100 == 0:
                                conn.commit()
                                current = count_hadiths()
                                print(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                                
                                if current >= TARGET:
                                    print(f"\n🎉 OBJECTIF ATTEINT: {current:,} hadiths!")
                                    conn.commit()
                                    conn.close()
                                    return total_inserted, total_skipped
                        else:
                            skipped += 1
                            total_skipped += 1
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                continue
        
        conn.commit()
        print(f"   ✅ {name}: +{inserted} nouveaux, {skipped} doublons évités")
    
    conn.close()
    return total_inserted, total_skipped

def harvest_sunnah_com():
    """Extraction depuis Sunnah.com API"""
    print("\n🔥 SUNNAH.COM API - Collections supplémentaires")
    
    collections = [
        ("bukhari", "Sahih Bukhari (EN)", 7563),
        ("muslim", "Sahih Muslim (EN)", 7563),
        ("nasai", "Sunan an-Nasa'i (EN)", 5761),
        ("abudawud", "Sunan Abu Dawud (EN)", 5274),
        ("tirmidhi", "Jami' at-Tirmidhi (EN)", 3956),
        ("ibnmajah", "Sunan Ibn Majah (EN)", 4341),
        ("malik", "Muwatta Malik (EN)", 1594),
        ("riyadussalihin", "Riyad as-Salihin", 1896),
        ("adab", "Al-Adab Al-Mufrad", 1322),
        ("bulugh", "Bulugh al-Maram", 1358),
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    total_inserted = 0
    total_skipped = 0
    
    for slug, name, max_num in collections:
        print(f"\n📖 {name} (max {max_num} hadiths)")
        inserted = 0
        skipped = 0
        
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
                    source_url = url
                    
                    if insert_hadith(cursor, name, num, matn_ar, isnad, grade, source_url, "sunnah_com"):
                        inserted += 1
                        total_inserted += 1
                        
                        if inserted % 50 == 0:
                            conn.commit()
                            current = count_hadiths()
                            print(f"   ✅ {inserted} nouveaux | Total DB: {current:,}")
                            
                            if current >= TARGET:
                                print(f"\n🎉 OBJECTIF ATTEINT: {current:,} hadiths!")
                                conn.commit()
                                conn.close()
                                return total_inserted, total_skipped
                    else:
                        skipped += 1
                        total_skipped += 1
                
                time.sleep(0.3)
                
            except Exception as e:
                continue
        
        conn.commit()
        print(f"   ✅ {name}: +{inserted} nouveaux, {skipped} doublons évités")
    
    conn.close()
    return total_inserted, total_skipped

def main():
    print("="*80)
    print("🚀 TURBO HARVESTER - EXTRACTION MAXIMALE VERS 110K")
    print("="*80)
    
    start_time = datetime.now()
    initial = count_hadiths()
    
    print(f"\n📊 État initial: {initial:,} hadiths")
    print(f"🎯 Objectif: {TARGET:,} hadiths")
    print(f"📈 Besoin: {TARGET - initial:,} hadiths")
    
    # Phase 1: Hadith Gading
    print("\n" + "="*80)
    print("PHASE 1: HADITH GADING API")
    print("="*80)
    inserted1, skipped1 = harvest_hadith_gading()
    
    current = count_hadiths()
    if current >= TARGET:
        print(f"\n🎉 OBJECTIF ATTEINT: {current:,} hadiths!")
        return
    
    # Phase 2: Sunnah.com
    print("\n" + "="*80)
    print("PHASE 2: SUNNAH.COM API")
    print("="*80)
    inserted2, skipped2 = harvest_sunnah_com()
    
    # Résumé final
    final = count_hadiths()
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 RÉSUMÉ FINAL")
    print("="*80)
    print(f"⏱️  Durée: {duration/60:.1f} minutes")
    print(f"📊 Initial: {initial:,} hadiths")
    print(f"📊 Final: {final:,} hadiths")
    print(f"✅ Ajoutés: {final - initial:,} hadiths")
    print(f"⏭️  Doublons évités: {skipped1 + skipped2:,}")
    print(f"🎯 Progression: {(final/TARGET)*100:.1f}%")
    
    if final >= TARGET:
        print(f"\n🎉 OBJECTIF 110K ATTEINT!")
    else:
        print(f"\n📈 Reste: {TARGET - final:,} hadiths")

if __name__ == "__main__":
    main()