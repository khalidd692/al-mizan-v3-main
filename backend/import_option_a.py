#!/usr/bin/env python3
"""
Import Option A - Collections spécialisées populaires
Riyad al-Salihin, 40 Hadiths, Bulugh al-Maram, Al-Adab al-Mufrad
"""

import sqlite3
import requests
import time
from datetime import datetime

# Configuration
DB_PATH = 'backend/almizane.db'
SUNNAH_API = 'https://api.sunnah.com/v1'

# Collections Option A
COLLECTIONS = {
    'riyadussalihin': {'name': 'Riyad al-Salihin', 'books': 19},
    'nawawi40': {'name': '40 Hadiths Nawawi', 'books': 1},
    'bulugh': {'name': 'Bulugh al-Maram', 'books': 16},
    'adab': {'name': 'Al-Adab al-Mufrad', 'books': 55}
}

def log(msg):
    """Affiche un message avec timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f'[{timestamp}] {msg}')
    
def import_collection(conn, collection_id, collection_info):
    """Importe une collection complète"""
    log(f"📚 Import de {collection_info['name']}...")
    cursor = conn.cursor()
    total_hadiths = 0
    errors = 0
    
    for book_num in range(1, collection_info['books'] + 1):
        try:
            url = f'{SUNNAH_API}/collections/{collection_id}/books/{book_num}/hadiths'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                hadiths = data.get('data', [])
                
                for hadith in hadiths:
                    try:
                        # Extraction des données
                        hadith_bodies = hadith.get('hadith', [])
                        arabic_text = hadith_bodies[0].get('body', '') if len(hadith_bodies) > 0 else ''
                        french_text = hadith_bodies[1].get('body', '') if len(hadith_bodies) > 1 else ''
                        
                        # Insertion
                        cursor.execute('''
                            INSERT OR IGNORE INTO hadiths 
                            (collection, livre, numero_hadith, matn_ar, matn_fr, grade_final)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            collection_info['name'],
                            str(book_num),
                            hadith.get('hadithNumber', ''),
                            arabic_text,
                            french_text,
                            hadith.get('grade', {}).get('grade', 'Non classé')
                        ))
                        total_hadiths += 1
                    except Exception as e:
                        errors += 1
                        continue
                
                conn.commit()
                log(f"  ✓ Livre {book_num}/{collection_info['books']}: {len(hadiths)} hadiths")
            else:
                log(f"  ⚠ Erreur HTTP {response.status_code} pour livre {book_num}")
                errors += 1
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            log(f"  ⚠ Erreur livre {book_num}: {str(e)}")
            errors += 1
            continue
    
    log(f"✅ {collection_info['name']}: {total_hadiths} hadiths importés ({errors} erreurs)")
    return total_hadiths

def main():
    """Fonction principale"""
    log('🚀 DÉMARRAGE IMPORT OPTION A')
    log('=' * 60)
    log('Collections à importer:')
    for coll_id, coll_info in COLLECTIONS.items():
        log(f"  - {coll_info['name']} ({coll_info['books']} livres)")
    log('=' * 60)
    log('')
    
    # Connexion à la base
    try:
        conn = sqlite3.connect(DB_PATH)
        log('✓ Connexion à la base de données établie')
    except Exception as e:
        log(f'❌ Erreur de connexion: {e}')
        return
    
    # Import des collections
    grand_total = 0
    start_time = time.time()
    
    for coll_id, coll_info in COLLECTIONS.items():
        count = import_collection(conn, coll_id, coll_info)
        grand_total += count
        log('')
    
    conn.close()
    
    # Statistiques finales
    elapsed = time.time() - start_time
    log('=' * 60)
    log(f'🎉 IMPORT TERMINÉ')
    log(f'⏱️  Durée: {elapsed/60:.1f} minutes')
    log(f'📊 Total importé: {grand_total:,} hadiths')
    log('=' * 60)
    log('')
    
    # Vérification finale
    log('📊 Vérification de la base...')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM hadiths')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT collection, COUNT(*) FROM hadiths GROUP BY collection')
        sources = cursor.fetchall()
        
        conn.close()
        
        log(f'✅ Total dans la base: {total:,} hadiths')
        log('')
        log('Répartition par collection:')
        for collection, count in sources:
            log(f'  - {collection}: {count:,} hadiths')
            
    except Exception as e:
        log(f'⚠ Erreur de vérification: {e}')

if __name__ == '__main__':
    main()