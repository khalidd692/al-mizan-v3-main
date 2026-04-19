#!/usr/bin/env python3
"""
🚀 HARVESTER SIMPLIFIÉ - OBJECTIF 110K HADITHS
Utilise l'API Hadith Gading pour compléter rapidement la base
"""

import sqlite3
import requests
import time
import hashlib
from datetime import datetime

class Simple110KHarvester:
    def __init__(self):
        self.db_path = "backend/almizane.db"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0'
        })
        
        self.stats = {
            'imported': 0,
            'duplicates': 0,
            'errors': 0
        }
        
    def get_hash(self, text):
        """Génère SHA256 pour détecter les doublons"""
        clean = ''.join(text.split()).lower()
        return hashlib.sha256(clean.encode()).hexdigest()
    
    def check_duplicate(self, sha256_hash):
        """Vérifie si le hadith existe déjà"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hadiths WHERE sha256 = ?", (sha256_hash,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists
    
    def save_hadith(self, hadith_data):
        """Sauvegarde un hadith"""
        sha256_hash = self.get_hash(hadith_data['matn_ar'])
        
        if self.check_duplicate(sha256_hash):
            self.stats['duplicates'] += 1
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO hadiths (
                    sha256, collection, numero_hadith, matn_ar,
                    isnad_brut, grade_final, source_url, source_api, inserted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sha256_hash,
                hadith_data.get('collection', 'unknown'),
                hadith_data.get('numero_hadith', ''),
                hadith_data['matn_ar'],
                hadith_data.get('isnad_brut', ''),
                hadith_data.get('grade_final', 'non_évalué'),
                hadith_data.get('source_url', ''),
                hadith_data.get('source_api', 'hadith_gading'),
                datetime.now().isoformat()
            ))
            conn.commit()
            self.stats['imported'] += 1
            return True
        except Exception as e:
            self.stats['errors'] += 1
            return False
        finally:
            conn.close()
    
    def harvest_collection(self, collection_id, collection_name, target):
        """Collecte une collection complète"""
        print(f"\n📖 Collection: {collection_name}")
        print(f"🎯 Objectif: {target} hadiths")
        
        count = 0
        page = 1
        
        while count < target:
            try:
                url = f"https://api.hadith.gading.dev/books/{collection_id}?range={page}-{page+9}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'hadiths' in data['data']:
                        hadiths = data['data']['hadiths']
                        
                        if not hadiths:
                            break
                        
                        for hadith in hadiths:
                            hadith_data = {
                                'collection': collection_name,
                                'numero_hadith': str(hadith.get('number', '')),
                                'matn_ar': hadith.get('arab', ''),
                                'isnad_brut': hadith.get('name', ''),
                                'grade_final': 'non_évalué',
                                'source_url': url,
                                'source_api': 'hadith_gading'
                            }
                            
                            if hadith_data['matn_ar'] and self.save_hadith(hadith_data):
                                count += 1
                                
                                if count % 500 == 0:
                                    print(f"   ✅ {count:,}/{target:,} hadiths")
                    else:
                        break
                else:
                    print(f"   ⚠️  Erreur HTTP {response.status_code}")
                    break
                
                page += 10
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"   ⚠️  Erreur: {e}")
                page += 10
                continue
        
        print(f"✅ {collection_name}: {count:,} hadiths collectés")
        return count
    
    def run(self):
        """Lance le harvesting"""
        print("\n" + "="*80)
        print("🚀 HARVESTER SIMPLIFIÉ - OBJECTIF 110K HADITHS")
        print("="*80)
        print(f"📅 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # État initial
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        initial_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Base actuelle: {initial_count:,} hadiths")
        print(f"🎯 Objectif: 110,000 hadiths")
        needed = 110000 - initial_count
        print(f"📈 Besoin: {needed:,} hadiths supplémentaires")
        
        start_time = time.time()
        
        # Collections à harvester (API Hadith Gading)
        collections = [
            ('ahmad', 'Musnad Ahmad', 15000),
            ('darimi', 'Sunan ad-Darimi', 3500),
            ('ibnmajah', 'Sunan Ibn Majah', 4500),
        ]
        
        print("\n" + "="*80)
        print("📚 HARVESTING DES COLLECTIONS")
        print("="*80)
        
        for coll_id, coll_name, target in collections:
            self.harvest_collection(coll_id, coll_name, target)
            
            # Vérifier si on a atteint l'objectif
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM hadiths")
            current_count = cursor.fetchone()[0]
            conn.close()
            
            if current_count >= 110000:
                print(f"\n🎉 OBJECTIF ATTEINT ! {current_count:,} hadiths")
                break
        
        # Rapport final
        duration = time.time() - start_time
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        final_count = cursor.fetchone()[0]
        conn.close()
        
        print("\n" + "="*80)
        print("📊 RAPPORT FINAL")
        print("="*80)
        print(f"⏱️  Durée: {duration/60:.1f} minutes")
        print(f"📊 Base initiale: {initial_count:,} hadiths")
        print(f"📊 Base finale: {final_count:,} hadiths")
        print(f"✅ Nouveaux hadiths: {self.stats['imported']:,}")
        print(f"⚠️  Doublons évités: {self.stats['duplicates']:,}")
        print(f"❌ Erreurs: {self.stats['errors']:,}")
        
        progress = (final_count / 110000) * 100
        print(f"\n🎯 Progression vers 110K: {progress:.1f}%")
        
        if final_count >= 110000:
            print("\n🎉 OBJECTIF ATTEINT ! 110,000 hadiths ✅")
        else:
            remaining = 110000 - final_count
            print(f"\n📌 Reste à collecter: {remaining:,} hadiths")

if __name__ == "__main__":
    harvester = Simple110KHarvester()
    harvester.run()