#!/usr/bin/env python3
"""
Mega Harvester Phase 2 - Import massif multi-sources
Objectif: Passer de 60K à 150K+ hadiths
"""

import sqlite3
import hashlib
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.connectors.hadith_gading_connector import HadithGadingConnector
from backend.connectors.jsdelivr_connector import JSDelivrConnector

class MegaHarvesterPhase2:
    """
    Harvester Phase 2 - Sources alternatives accessibles
    
    Stratégie:
    1. Compléter hadith-gading.com (Musnad Ahmad restant)
    2. Explorer datasets GitHub supplémentaires
    3. Utiliser APIs publiques accessibles
    4. Importer collections spécialisées
    """
    
    def __init__(self, db_path: str = 'backend/almizane.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Connecteurs
        self.hadith_gading = HadithGadingConnector()
        self.jsdelivr = JSDelivrConnector()
        
        # Statistiques
        self.stats = {
            'total_imported': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'by_source': {}
        }
    
    def get_current_count(self) -> int:
        """Compte actuel de hadiths"""
        self.cursor.execute('SELECT COUNT(*) FROM hadiths')
        return self.cursor.fetchone()[0]
    
    def hadith_exists(self, sha256: str) -> bool:
        """Vérifie si un hadith existe déjà"""
        self.cursor.execute('SELECT 1 FROM hadiths WHERE sha256 = ? LIMIT 1', (sha256,))
        return self.cursor.fetchone() is not None
    
    def insert_hadith(self, hadith: Dict) -> bool:
        """
        Insère un hadith dans la base
        
        Returns:
            True si inséré, False si doublon
        """
        # Vérifier doublon
        if self.hadith_exists(hadith['sha256']):
            self.stats['duplicates_skipped'] += 1
            return False
        
        try:
            self.cursor.execute('''
                INSERT INTO hadiths (
                    sha256, collection, numero_hadith, livre, chapitre,
                    matn_ar, matn_fr, isnad_brut, grade_final, categorie,
                    badge_alerte, source_url, source_api, inserted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hadith['sha256'],
                hadith['collection'],
                hadith['numero_hadith'],
                hadith['livre'],
                hadith['chapitre'],
                hadith['matn_ar'],
                hadith['matn_fr'],
                hadith['isnad_brut'],
                hadith['grade_final'],
                hadith['categorie'],
                hadith['badge_alerte'],
                hadith['source_url'],
                hadith['source_api'],
                hadith['inserted_at']
            ))
            
            self.stats['total_imported'] += 1
            
            # Compter par source
            source = hadith['source_api']
            self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def phase2_hadith_gading_complete(self):
        """
        Phase 2A: Compléter hadith-gading.com
        Importer les collections restantes
        """
        print("\n" + "="*80)
        print("📚 PHASE 2A: Compléter hadith-gading.com")
        print("="*80)
        
        # Collections à compléter
        remaining_collections = [
            ('musnad-ahmad', 'Musnad Ahmad', 27000),
            ('sunan-darimi', 'Sunan al-Darimi', 3500),
            ('muwatta-malik', 'Muwatta Malik', 2000),
        ]
        
        for slug, name, estimated in remaining_collections:
            print(f"\n📖 {name} (estimation: {estimated:,} hadiths)")
            
            try:
                hadiths = self.hadith_gading.harvest_collection(slug, name)
                
                imported = 0
                for hadith in hadiths:
                    if self.insert_hadith(hadith):
                        imported += 1
                        if imported % 100 == 0:
                            self.conn.commit()
                            print(f"   ✅ {imported:,} hadiths importés...")
                
                self.conn.commit()
                print(f"✅ {name}: {imported:,} hadiths importés")
                
            except Exception as e:
                print(f"❌ Erreur {name}: {e}")
    
    def phase2_github_datasets(self):
        """
        Phase 2B: Importer datasets GitHub supplémentaires
        """
        print("\n" + "="*80)
        print("📦 PHASE 2B: Datasets GitHub supplémentaires")
        print("="*80)
        
        # Datasets GitHub identifiés
        github_datasets = [
            {
                'repo': 'sunnah-com/hadith',
                'files': ['bukhari.json', 'muslim.json', 'abudawud.json'],
                'description': 'Sunnah.com dataset'
            },
            {
                'repo': 'islamic-network/hadith-api',
                'files': ['data/bukhari.json', 'data/muslim.json'],
                'description': 'Islamic Network API'
            },
            {
                'repo': 'hadith-api/hadith-api',
                'files': ['collections/*.json'],
                'description': 'Hadith API collections'
            }
        ]
        
        for dataset in github_datasets:
            print(f"\n📦 {dataset['description']}")
            print(f"   Repo: {dataset['repo']}")
            
            try:
                # Utiliser jsdelivr pour accéder aux fichiers
                for file_path in dataset['files']:
                    url = f"https://cdn.jsdelivr.net/gh/{dataset['repo']}@main/{file_path}"
                    print(f"   Téléchargement: {file_path}...")
                    
                    hadiths = self.jsdelivr.fetch_and_parse(url)
                    
                    if hadiths:
                        imported = 0
                        for hadith in hadiths:
                            if self.insert_hadith(hadith):
                                imported += 1
                        
                        self.conn.commit()
                        print(f"   ✅ {imported:,} hadiths importés")
                    else:
                        print(f"   ⚠️ Aucun hadith trouvé")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    def phase2_specialized_collections(self):
        """
        Phase 2C: Collections spécialisées
        """
        print("\n" + "="*80)
        print("📚 PHASE 2C: Collections spécialisées")
        print("="*80)
        
        # Collections spécialisées accessibles
        specialized = [
            {
                'name': 'Riyad al-Salihin',
                'url': 'https://cdn.jsdelivr.net/gh/islamic-network/hadith-api@main/data/riyad-as-salihin.json',
                'estimated': 1900
            },
            {
                'name': 'Bulugh al-Maram',
                'url': 'https://cdn.jsdelivr.net/gh/islamic-network/hadith-api@main/data/bulugh-al-maram.json',
                'estimated': 1500
            },
            {
                'name': 'Al-Adab al-Mufrad',
                'url': 'https://cdn.jsdelivr.net/gh/islamic-network/hadith-api@main/data/al-adab-al-mufrad.json',
                'estimated': 1300
            }
        ]
        
        for collection in specialized:
            print(f"\n📖 {collection['name']} (estimation: {collection['estimated']:,})")
            
            try:
                hadiths = self.jsdelivr.fetch_and_parse(collection['url'])
                
                if hadiths:
                    imported = 0
                    for hadith in hadiths:
                        if self.insert_hadith(hadith):
                            imported += 1
                    
                    self.conn.commit()
                    print(f"✅ {imported:,} hadiths importés")
                else:
                    print("⚠️ Collection non disponible")
                    
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def run_full_phase2(self):
        """
        Exécute la Phase 2 complète
        """
        start_time = time.time()
        initial_count = self.get_current_count()
        
        print("\n" + "="*80)
        print("🚀 MEGA HARVESTER PHASE 2 - DÉMARRAGE")
        print("="*80)
        print(f"Base actuelle: {initial_count:,} hadiths")
        print(f"Objectif: 150,000 hadiths")
        print(f"Restant: {150000 - initial_count:,} hadiths")
        print()
        
        # Phase 2A: Compléter hadith-gading
        self.phase2_hadith_gading_complete()
        
        # Phase 2B: GitHub datasets
        self.phase2_github_datasets()
        
        # Phase 2C: Collections spécialisées
        self.phase2_specialized_collections()
        
        # Rapport final
        final_count = self.get_current_count()
        duration = time.time() - start_time
        
        print("\n" + "="*80)
        print("✅ PHASE 2 TERMINÉE")
        print("="*80)
        print(f"Hadiths initiaux:  {initial_count:,}")
        print(f"Hadiths finaux:    {final_count:,}")
        print(f"Nouveaux imports:  {final_count - initial_count:,}")
        print(f"Doublons évités:   {self.stats['duplicates_skipped']:,}")
        print(f"Erreurs:           {self.stats['errors']}")
        print(f"Durée:             {duration/60:.1f} minutes")
        print()
        print("Répartition par source:")
        for source, count in self.stats['by_source'].items():
            print(f"  {source:30s}: {count:>6,} hadiths")
        print()
        print(f"Progression: {(final_count/150000)*100:.1f}% de l'objectif 150K")
        print("="*80)
        
        self.conn.close()

def main():
    """Point d'entrée principal"""
    harvester = MegaHarvesterPhase2()
    harvester.run_full_phase2()

if __name__ == '__main__':
    main()