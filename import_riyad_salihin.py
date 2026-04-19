#!/usr/bin/env python3
"""
Import de Riyad al-Salihin (~1,900 hadiths)
Recueil très populaire de hadiths sur les bonnes manières et la spiritualité
"""

import sys
import sqlite3
import hashlib
from pathlib import Path

# Ajouter le dossier backend au path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from connectors.sunnah_connector import SunnahConnector

def create_hash(text: str) -> str:
    """Crée un hash SHA-256 du texte"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def check_duplicate(cursor, matn_hash: str) -> bool:
    """Vérifie si un hadith existe déjà"""
    cursor.execute(
        "SELECT COUNT(*) FROM hadiths WHERE matn_hash = ?",
        (matn_hash,)
    )
    return cursor.fetchone()[0] > 0

def import_riyad_salihin():
    """Import Riyad al-Salihin dans la base de données"""
    
    print("=" * 70)
    print("📚 IMPORT RIYAD AL-SALIHIN")
    print("=" * 70)
    print()
    
    # Connexion à la base de données
    db_path = Path(__file__).parent / 'backend' / 'almizane.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier l'état actuel
    cursor.execute("""
        SELECT COUNT(*) FROM hadiths 
        WHERE collection = 'riyad_salihin'
    """)
    existing = cursor.fetchone()[0]
    
    print(f"📊 État actuel : {existing} hadiths de Riyad al-Salihin en base")
    print()
    
    if existing > 0:
        response = input("⚠️  Des hadiths existent déjà. Continuer ? (o/n) : ")
        if response.lower() != 'o':
            print("❌ Import annulé")
            return
    
    # Initialiser le connecteur
    connector = SunnahConnector()
    
    # Récupérer tous les hadiths
    print("🔄 Récupération des hadiths depuis sunnah.com...")
    print("⏱️  Temps estimé : ~15-20 minutes (1,900 hadiths)")
    print()
    
    hadiths = connector.get_all_hadiths('riyadussalihin', delay=0.5)
    
    if not hadiths:
        print("❌ Aucun hadith récupéré")
        return
    
    print()
    print("=" * 70)
    print("💾 INSERTION DANS LA BASE DE DONNÉES")
    print("=" * 70)
    print()
    
    # Insérer les hadiths
    inserted = 0
    duplicates = 0
    errors = 0
    
    for i, hadith in enumerate(hadiths, 1):
        try:
            # Créer le hash du matn arabe
            matn_hash = create_hash(hadith['matn_ar'])
            
            # Vérifier les doublons
            if check_duplicate(cursor, matn_hash):
                duplicates += 1
                continue
            
            # Insérer le hadith
            cursor.execute("""
                INSERT INTO hadiths (
                    collection,
                    numero_hadith,
                    matn_ar,
                    matn_en,
                    grade_final,
                    reference,
                    source_api,
                    matn_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hadith['collection'],
                hadith['numero_hadith'],
                hadith['matn_ar'],
                hadith['matn_en'],
                hadith['grade_final'],
                hadith['reference'],
                hadith['source_api'],
                matn_hash
            ))
            
            inserted += 1
            
            if i % 100 == 0:
                conn.commit()
                print(f"✅ {i}/{len(hadiths)} hadiths traités ({inserted} insérés, {duplicates} doublons)")
        
        except Exception as e:
            errors += 1
            print(f"❌ Erreur hadith {i}: {e}")
    
    # Commit final
    conn.commit()
    
    # Statistiques finales
    print()
    print("=" * 70)
    print("📊 RÉSULTATS DE L'IMPORT")
    print("=" * 70)
    print(f"✅ Hadiths insérés : {inserted}")
    print(f"⚠️  Doublons évités : {duplicates}")
    print(f"❌ Erreurs : {errors}")
    print()
    
    # Vérification finale
    cursor.execute("""
        SELECT COUNT(*) FROM hadiths 
        WHERE collection = 'riyad_salihin'
    """)
    total = cursor.fetchone()[0]
    
    print(f"📚 Total Riyad al-Salihin en base : {total} hadiths")
    print()
    
    # Statistiques globales
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    total_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT collection) FROM hadiths")
    collections = cursor.fetchone()[0]
    
    print("=" * 70)
    print("📊 ÉTAT GLOBAL DE LA BASE")
    print("=" * 70)
    print(f"📚 Total hadiths : {total_db:,}")
    print(f"📖 Collections : {collections}")
    print()
    
    # Top collections
    cursor.execute("""
        SELECT collection, COUNT(*) as count
        FROM hadiths
        GROUP BY collection
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print("🏆 Top 10 des collections :")
    for collection, count in cursor.fetchall():
        print(f"   • {collection}: {count:,} hadiths")
    
    conn.close()
    
    print()
    print("=" * 70)
    print("✅ IMPORT TERMINÉ AVEC SUCCÈS")
    print("=" * 70)
    print()
    print("📝 Prochaines étapes recommandées :")
    print("   1. Bulugh al-Maram (~1,500 hadiths)")
    print("   2. Al-Adab al-Mufrad (~1,300 hadiths)")
    print()

if __name__ == '__main__':
    try:
        import_riyad_salihin()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()