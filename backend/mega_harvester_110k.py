#!/usr/bin/env python3
"""
🚀 MEGA HARVESTER - OBJECTIF 110K HADITHS
Combine 3 sources pour atteindre 110,000 hadiths d'ici fin avril 2026
"""

import sqlite3
import requests
import time
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import json

class MegaHarvester110K:
    def __init__(self):
        self.db_path = "backend/almizane.db"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Statistiques
        self.stats = {
            'dorar': 0,
            'musnad_ahmad': 0,
            'hadeethenc': 0,
            'duplicates': 0,
            'errors': 0
        }
        
    def get_hash(self, text):
        """Génère un hash unique pour détecter les doublons"""
        clean = ''.join(text.split()).lower()
        return hashlib.md5(clean.encode()).hexdigest()
    
    def check_duplicate(self, text_hash):
        """Vérifie si le hadith existe déjà"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Vérifier d'abord quelle colonne existe
        cursor.execute("PRAGMA table_info(hadiths)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'text_hash' in columns:
            cursor.execute("SELECT COUNT(*) FROM hadiths WHERE text_hash = ?", (text_hash,))
        elif 'matn_ar_hash' in columns:
            cursor.execute("SELECT COUNT(*) FROM hadiths WHERE matn_ar_hash = ?", (text_hash,))
        else:
            # Pas de colonne hash, on ne peut pas vérifier les doublons
            conn.close()
            return False
            
        exists = cursor.fetchone()[0] > 0
        conn.close()
        return exists
    
    def save_hadith(self, hadith_data):
        """Sauvegarde un hadith dans la base"""
        text_hash = self.get_hash(hadith_data['text'])
        
        if self.check_duplicate(text_hash):
            self.stats['duplicates'] += 1
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Vérifier quelle colonne hash existe
            cursor.execute("PRAGMA table_info(hadiths)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'text_hash' in columns:
                cursor.execute("""
                    INSERT INTO hadiths (
                        collection, hadith_number, text, narrator,
                        grade, text_hash, source_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hadith_data.get('collection', 'unknown'),
                    hadith_data.get('number', 0),
                    hadith_data['text'],
                    hadith_data.get('narrator', ''),
                    hadith_data.get('grade', 'non_évalué'),
                    text_hash,
                    hadith_data.get('source_url', ''),
                    datetime.now().isoformat()
                ))
            elif 'matn_ar_hash' in columns:
                cursor.execute("""
                    INSERT INTO hadiths (
                        collection, hadith_number, text, narrator,
                        grade, matn_ar_hash, source_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hadith_data.get('collection', 'unknown'),
                    hadith_data.get('number', 0),
                    hadith_data['text'],
                    hadith_data.get('narrator', ''),
                    hadith_data.get('grade', 'non_évalué'),
                    text_hash,
                    hadith_data.get('source_url', ''),
                    datetime.now().isoformat()
                ))
            else:
                # Pas de colonne hash, insertion sans hash
                cursor.execute("""
                    INSERT INTO hadiths (
                        collection, hadith_number, text, narrator,
                        grade, source_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    hadith_data.get('collection', 'unknown'),
                    hadith_data.get('number', 0),
                    hadith_data['text'],
                    hadith_data.get('narrator', ''),
                    hadith_data.get('grade', 'non_évalué'),
                    hadith_data.get('source_url', ''),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            self.stats['errors'] += 1
            return False
        finally:
            conn.close()
    
    def harvest_dorar_html(self, target=15000):
        """
        SOURCE 1: Dorar.net via HTML parsing
        Objectif: +15,000 hadiths
        """
        print("\n" + "="*80)
        print("📖 SOURCE 1: DORAR.NET (HTML Parser)")
        print("="*80)
        
        keywords = [
            'الصلاة', 'الزكاة', 'الصيام', 'الحج', 'الإيمان',
            'التوحيد', 'الجهاد', 'البر', 'الصدق', 'الأمانة',
            'العلم', 'الذكر', 'الدعاء', 'التوبة', 'الصبر',
            'الشكر', 'الرضا', 'التوكل', 'الإخلاص', 'الخشوع'
        ]
        
        count = 0
        for keyword in keywords:
            if count >= target:
                break
                
            print(f"\n🔍 Recherche: {keyword}")
            
            try:
                url = f"https://dorar.net/hadith/search?q={keyword}&page=1"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    hadith_cards = soup.find_all('div', class_='hadith-card')
                    
                    for card in hadith_cards[:100]:  # Max 100 par recherche
                        try:
                            text_elem = card.find('div', class_='hadith-text')
                            grade_elem = card.find('span', class_='grade')
                            
                            if text_elem:
                                hadith_data = {
                                    'collection': 'dorar',
                                    'text': text_elem.get_text(strip=True),
                                    'grade': grade_elem.get_text(strip=True) if grade_elem else 'non_évalué',
                                    'source_url': url
                                }
                                
                                if self.save_hadith(hadith_data):
                                    count += 1
                                    self.stats['dorar'] += 1
                                    
                                    if count % 100 == 0:
                                        print(f"   ✅ {count}/{target} hadiths")
                        except Exception as e:
                            continue
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ⚠️  Erreur: {e}")
                continue
        
        print(f"\n✅ Dorar.net: {self.stats['dorar']} hadiths collectés")
        return self.stats['dorar']
    
    def harvest_musnad_ahmad(self, target=20000):
        """
        SOURCE 2: Musnad Ahmad (complétion)
        Objectif: +20,000 hadiths
        """
        print("\n" + "="*80)
        print("📖 SOURCE 2: MUSNAD AHMAD (Complétion)")
        print("="*80)
        
        # Vérifier combien on a déjà
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hadiths WHERE collection = 'Musnad Ahmad'")
        current = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Actuellement: {current} hadiths Musnad Ahmad")
        needed = target - current
        print(f"🎯 Objectif: +{needed} hadiths supplémentaires")
        
        # API Hadith Gading pour Musnad Ahmad
        count = 0
        page = 1
        
        while count < needed:
            try:
                url = f"https://api.hadith.gading.dev/books/ahmad?range={page}-{page+9}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'hadiths' in data['data']:
                        for hadith in data['data']['hadiths']:
                            hadith_data = {
                                'collection': 'Musnad Ahmad',
                                'number': hadith.get('number', 0),
                                'text': hadith.get('arab', ''),
                                'narrator': hadith.get('name', ''),
                                'grade': 'non_évalué',
                                'source_url': url
                            }
                            
                            if self.save_hadith(hadith_data):
                                count += 1
                                self.stats['musnad_ahmad'] += 1
                                
                                if count % 100 == 0:
                                    print(f"   ✅ {count}/{needed} hadiths")
                    else:
                        break
                
                page += 10
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ⚠️  Erreur page {page}: {e}")
                page += 10
                continue
        
        print(f"\n✅ Musnad Ahmad: {self.stats['musnad_ahmad']} hadiths collectés")
        return self.stats['musnad_ahmad']
    
    def harvest_hadeethenc(self, target=10000):
        """
        SOURCE 3: HadeethEnc.com
        Objectif: +10,000 hadiths
        """
        print("\n" + "="*80)
        print("📖 SOURCE 3: HADEETHENC.COM")
        print("="*80)
        
        categories = [
            'faith', 'prayer', 'zakat', 'fasting', 'hajj',
            'jihad', 'knowledge', 'manners', 'family', 'business'
        ]
        
        count = 0
        for category in categories:
            if count >= target:
                break
                
            print(f"\n🔍 Catégorie: {category}")
            
            try:
                url = f"https://hadeethenc.com/api/v1/hadeeths/list?language=ar&category={category}&per_page=100"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data:
                        for item in data['data']:
                            hadith_data = {
                                'collection': 'hadeethenc',
                                'text': item.get('hadeeth', ''),
                                'narrator': item.get('attribution', ''),
                                'grade': item.get('grade', 'non_évalué'),
                                'source_url': url
                            }
                            
                            if self.save_hadith(hadith_data):
                                count += 1
                                self.stats['hadeethenc'] += 1
                                
                                if count % 100 == 0:
                                    print(f"   ✅ {count}/{target} hadiths")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️  Erreur: {e}")
                continue
        
        print(f"\n✅ HadeethEnc: {self.stats['hadeethenc']} hadiths collectés")
        return self.stats['hadeethenc']
    
    def run(self):
        """Lance le harvesting complet"""
        print("\n" + "="*80)
        print("🚀 MEGA HARVESTER - OBJECTIF 110K HADITHS")
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
        print(f"📈 Besoin: {110000 - initial_count:,} hadiths supplémentaires")
        
        start_time = time.time()
        
        # Phase 1: Dorar.net (+15K)
        self.harvest_dorar_html(15000)
        
        # Phase 2: Musnad Ahmad (+20K)
        self.harvest_musnad_ahmad(20000)
        
        # Phase 3: HadeethEnc (+10K)
        self.harvest_hadeethenc(10000)
        
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
        print(f"✅ Nouveaux hadiths: {final_count - initial_count:,}")
        print(f"\n📈 Détail par source:")
        print(f"   • Dorar.net: {self.stats['dorar']:,}")
        print(f"   • Musnad Ahmad: {self.stats['musnad_ahmad']:,}")
        print(f"   • HadeethEnc: {self.stats['hadeethenc']:,}")
        print(f"\n⚠️  Doublons évités: {self.stats['duplicates']:,}")
        print(f"❌ Erreurs: {self.stats['errors']:,}")
        
        progress = (final_count / 110000) * 100
        print(f"\n🎯 Progression vers 110K: {progress:.1f}%")
        
        if final_count >= 110000:
            print("\n🎉 OBJECTIF ATTEINT ! 110,000 hadiths ✅")
        else:
            remaining = 110000 - final_count
            print(f"\n📌 Reste à collecter: {remaining:,} hadiths")

if __name__ == "__main__":
    harvester = MegaHarvester110K()
    harvester.run()