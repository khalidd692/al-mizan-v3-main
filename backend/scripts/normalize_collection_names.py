#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de normalisation des noms de collections
Résout le problème d'autorisation de 46% en standardisant les noms
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Mapping de normalisation des collections
COLLECTION_MAPPINGS = {
    # Bukhari - toutes les variations vers le nom canonique
    'bukhari': 'Sahih al-Bukhari',
    'sahih bukhari': 'Sahih al-Bukhari',
    'sahih al bukhari': 'Sahih al-Bukhari',
    'al-bukhari': 'Sahih al-Bukhari',
    'صحيح البخاري': 'Sahih al-Bukhari',
    
    # Muslim - toutes les variations
    'muslim': 'Sahih Muslim',
    'sahih muslim': 'Sahih Muslim',
    'al-muslim': 'Sahih Muslim',
    'صحيح مسلم': 'Sahih Muslim',
    
    # Abu Dawud
    'abu dawud': 'Sunan Abu Dawud',
    'abu dawood': 'Sunan Abu Dawud',
    'sunan abu dawud': 'Sunan Abu Dawud',
    'sunan abi dawud': 'Sunan Abu Dawud',
    'سنن أبي داود': 'Sunan Abu Dawud',
    
    # Tirmidhi
    'tirmidhi': 'Jami at-Tirmidhi',
    'al-tirmidhi': 'Jami at-Tirmidhi',
    'jami tirmidhi': 'Jami at-Tirmidhi',
    'sunan tirmidhi': 'Jami at-Tirmidhi',
    'جامع الترمذي': 'Jami at-Tirmidhi',
    
    # Nasa'i
    "nasa'i": "Sunan an-Nasa'i",
    'nasai': "Sunan an-Nasa'i",
    'al-nasai': "Sunan an-Nasa'i",
    'sunan nasai': "Sunan an-Nasa'i",
    'سنن النسائي': "Sunan an-Nasa'i",
    
    # Ibn Majah
    'ibn majah': 'Sunan Ibn Majah',
    'ibn maja': 'Sunan Ibn Majah',
    'sunan ibn majah': 'Sunan Ibn Majah',
    'سنن ابن ماجه': 'Sunan Ibn Majah',
    
    # Malik
    'malik': 'Muwatta Malik',
    'muwatta': 'Muwatta Malik',
    'muwatta malik': 'Muwatta Malik',
    'al-muwatta': 'Muwatta Malik',
    'الموطأ': 'Muwatta Malik',
    
    # Ahmad
    'ahmad': 'Musnad Ahmad',
    'musnad ahmad': 'Musnad Ahmad',
    'musnad imam ahmad': 'Musnad Ahmad',
    'مسند أحمد': 'Musnad Ahmad',
    
    # Darimi
    'darimi': 'Sunan ad-Darimi',
    'al-darimi': 'Sunan ad-Darimi',
    'sunan darimi': 'Sunan ad-Darimi',
    'سنن الدارمي': 'Sunan ad-Darimi',
    
    # 40 Nawawi
    '40 hadith': '40 Hadith Nawawi',
    'forty hadith': '40 Hadith Nawawi',
    'nawawi': '40 Hadith Nawawi',
    'an-nawawi': '40 Hadith Nawawi',
    'الأربعون النووية': '40 Hadith Nawawi',
    
    # Riyad as-Salihin
    'riyad': 'Riyad as-Salihin',
    'riyadh': 'Riyad as-Salihin',
    'riyad salihin': 'Riyad as-Salihin',
    'riyadh as-salihin': 'Riyad as-Salihin',
    'رياض الصالحين': 'Riyad as-Salihin',
    
    # Bulugh al-Maram
    'bulugh': 'Bulugh al-Maram',
    'bulugh maram': 'Bulugh al-Maram',
    'bulugh al-maram': 'Bulugh al-Maram',
    'بلوغ المرام': 'Bulugh al-Maram',
}

class CollectionNormalizer:
    """Normalise les noms de collections dans la base de données"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.mappings = COLLECTION_MAPPINGS
    
    def normalize_name(self, collection_name: str) -> str:
        """
        Normalise un nom de collection
        
        Args:
            collection_name: Nom original de la collection
            
        Returns:
            Nom normalisé ou nom original si pas de mapping
        """
        if not collection_name:
            return collection_name
        
        # Recherche exacte (insensible à la casse)
        lower_name = collection_name.lower().strip()
        if lower_name in self.mappings:
            return self.mappings[lower_name]
        
        # Recherche partielle
        for variant, canonical in self.mappings.items():
            if variant in lower_name or lower_name in variant:
                return canonical
        
        return collection_name
    
    def analyze_collections(self) -> Dict:
        """Analyse les collections actuelles et leurs variations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT collection, COUNT(*) as count
            FROM hadiths
            WHERE collection IS NOT NULL
            GROUP BY collection
            ORDER BY count DESC
        """)
        
        collections = []
        total_hadiths = 0
        normalizable_count = 0
        
        for row in cursor.fetchall():
            original = row[0]
            count = row[1]
            normalized = self.normalize_name(original)
            will_change = (normalized != original)
            
            collections.append({
                'original': original,
                'normalized': normalized,
                'count': count,
                'will_change': will_change
            })
            
            total_hadiths += count
            if will_change:
                normalizable_count += count
        
        conn.close()
        
        return {
            'collections': collections,
            'total_hadiths': total_hadiths,
            'normalizable_count': normalizable_count,
            'normalizable_percentage': (normalizable_count / total_hadiths * 100) if total_hadiths > 0 else 0
        }
    
    def apply_normalization(self, dry_run: bool = True) -> Dict:
        """
        Applique la normalisation des noms de collections
        
        Args:
            dry_run: Si True, simule sans modifier la base
            
        Returns:
            Rapport des modifications
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupérer toutes les collections uniques
        cursor.execute("""
            SELECT DISTINCT collection
            FROM hadiths
            WHERE collection IS NOT NULL
        """)
        
        updates = []
        total_updated = 0
        
        for (original,) in cursor.fetchall():
            normalized = self.normalize_name(original)
            
            if normalized != original:
                # Compter combien de hadiths seront affectés
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM hadiths
                    WHERE collection = ?
                """, (original,))
                
                count = cursor.fetchone()[0]
                
                updates.append({
                    'original': original,
                    'normalized': normalized,
                    'affected_hadiths': count
                })
                
                total_updated += count
                
                # Appliquer la mise à jour si pas en dry_run
                if not dry_run:
                    cursor.execute("""
                        UPDATE hadiths
                        SET collection = ?
                        WHERE collection = ?
                    """, (normalized, original))
        
        if not dry_run:
            conn.commit()
        
        conn.close()
        
        return {
            'dry_run': dry_run,
            'updates': updates,
            'total_collections_updated': len(updates),
            'total_hadiths_updated': total_updated
        }
    
    def verify_normalization(self) -> Dict:
        """Vérifie l'impact de la normalisation sur le taux d'autorisation"""
        import sys
        from pathlib import Path
        
        # Ajouter le répertoire backend au path
        backend_path = Path(__file__).parent.parent
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        from corpus_validator import CorpusValidator
        
        validator = CorpusValidator(self.db_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT collection, COUNT(*) as count
            FROM hadiths
            GROUP BY collection
        """)
        
        before_authorized = 0
        after_authorized = 0
        total = 0
        
        for row in cursor.fetchall():
            collection = row[0] or 'Unknown'
            count = row[1]
            total += count
            
            # Avant normalisation
            is_auth_before, _ = validator.is_authorized_source(collection)
            if is_auth_before:
                before_authorized += count
            
            # Après normalisation
            normalized = self.normalize_name(collection)
            is_auth_after, _ = validator.is_authorized_source(normalized)
            if is_auth_after:
                after_authorized += count
        
        conn.close()
        
        return {
            'total_hadiths': total,
            'before': {
                'authorized': before_authorized,
                'rate': (before_authorized / total * 100) if total > 0 else 0
            },
            'after': {
                'authorized': after_authorized,
                'rate': (after_authorized / total * 100) if total > 0 else 0
            },
            'improvement': {
                'additional_authorized': after_authorized - before_authorized,
                'rate_increase': ((after_authorized - before_authorized) / total * 100) if total > 0 else 0
            }
        }

def main():
    """Point d'entrée principal"""
    normalizer = CollectionNormalizer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "analyze":
            print("\n" + "="*80)
            print("📊 ANALYSE DES COLLECTIONS")
            print("="*80)
            
            analysis = normalizer.analyze_collections()
            
            print(f"\nTotal hadiths: {analysis['total_hadiths']:,}")
            print(f"Hadiths normalisables: {analysis['normalizable_count']:,} ({analysis['normalizable_percentage']:.1f}%)")
            
            print("\n📋 Collections à normaliser:")
            for col in analysis['collections']:
                if col['will_change']:
                    print(f"\n  ❌ '{col['original']}' ({col['count']:,} hadiths)")
                    print(f"  ✅ → '{col['normalized']}'")
        
        elif command == "verify":
            print("\n" + "="*80)
            print("🔍 VÉRIFICATION DE L'IMPACT")
            print("="*80)
            
            verification = normalizer.verify_normalization()
            
            print(f"\nTotal hadiths: {verification['total_hadiths']:,}")
            print(f"\n📉 AVANT normalisation:")
            print(f"   Autorisés: {verification['before']['authorized']:,} ({verification['before']['rate']:.1f}%)")
            
            print(f"\n📈 APRÈS normalisation:")
            print(f"   Autorisés: {verification['after']['authorized']:,} ({verification['after']['rate']:.1f}%)")
            
            print(f"\n✨ AMÉLIORATION:")
            print(f"   +{verification['improvement']['additional_authorized']:,} hadiths autorisés")
            print(f"   +{verification['improvement']['rate_increase']:.1f}% de taux d'autorisation")
        
        elif command == "apply":
            dry_run = "--dry-run" in sys.argv
            
            print("\n" + "="*80)
            if dry_run:
                print("🔍 SIMULATION DE NORMALISATION (DRY RUN)")
            else:
                print("⚠️  APPLICATION DE LA NORMALISATION")
            print("="*80)
            
            result = normalizer.apply_normalization(dry_run=dry_run)
            
            print(f"\nCollections à mettre à jour: {result['total_collections_updated']}")
            print(f"Hadiths affectés: {result['total_hadiths_updated']:,}")
            
            if result['updates']:
                print("\n📝 Modifications:")
                for update in result['updates'][:10]:  # Afficher les 10 premières
                    print(f"\n  '{update['original']}'")
                    print(f"  → '{update['normalized']}'")
                    print(f"  ({update['affected_hadiths']:,} hadiths)")
                
                if len(result['updates']) > 10:
                    print(f"\n  ... et {len(result['updates']) - 10} autres modifications")
            
            if dry_run:
                print("\n💡 Pour appliquer réellement: python backend/scripts/normalize_collection_names.py apply")
            else:
                print("\n✅ Normalisation appliquée avec succès!")
                print("\n🔄 Vérifiez l'impact avec: python backend/scripts/normalize_collection_names.py verify")
    
    else:
        print("\n" + "="*80)
        print("🔧 NORMALISATEUR DE NOMS DE COLLECTIONS")
        print("="*80)
        print("\nUsage:")
        print("  python backend/scripts/normalize_collection_names.py analyze")
        print("    → Analyse les collections à normaliser")
        print("\n  python backend/scripts/normalize_collection_names.py verify")
        print("    → Vérifie l'impact sur le taux d'autorisation")
        print("\n  python backend/scripts/normalize_collection_names.py apply --dry-run")
        print("    → Simule la normalisation sans modifier la base")
        print("\n  python backend/scripts/normalize_collection_names.py apply")
        print("    → Applique la normalisation (MODIFIE LA BASE)")
        print("\n" + "="*80)

if __name__ == "__main__":
    main()