#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de correction et harvesting - Phase 2
Corrige les bugs identifiés et relance l'import massif
"""

import sqlite3
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.connectors.hadith_gading_connector import HadithGadingConnector
from backend.connectors.jsdelivr_connector import JSDelivrConnector

class FixedHarvester:
    """
    Harvester corrigé avec gestion d'erreurs robuste
    """
    
    def __init__(self, db_path: str = 'backend/almizane.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Vérifier que la colonne sha256 existe
        self._ensure_sha256_column()
        
        # Connecteurs
        self.hadith_gading = HadithGadingConnector()
        self.jsdelivr = JSDelivrConnector()
        
        # Statistiques
        self.stats = {
            'total_imported': 0,
            'duplicates_skipped': 0,
            'errors': 0,
            'by_source': {},
            'by_collection': {}
        }
    
    def _ensure_sha256_column(self):
        """Vérifie et ajoute la colonne sha256 si nécessaire"""
        try:
            self.cursor.execute("SELECT sha256 FROM hadiths LIMIT 1")
        except sqlite3.OperationalError:
            print("⚠️  Colonne sha256 manquante, ajout en cours...")
            self.cursor.execute("ALTER TABLE hadiths ADD COLUMN sha256 TEXT")
            self.conn.commit()
            print("✅ Colonne sha256 ajoutée")
    
    def get_current_count(self) -> int:
        """Compte actuel de hadiths"""
        self.cursor.execute('SELECT COUNT(*) FROM hadiths')
        return self.cursor.fetchone()[0]
    
    def calculate_sha256(self, text_arabic: str, collection: str, hadith_number: int) -> str:
        """Calcule le SHA256 d'un hadith"""
        content = f"{collection}:{hadith_number}:{text_arabic}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def hadith_exists(self, sha256: str) -> bool:
        """Vérifie si un hadith existe déjà"""
        self.cursor.execute('SELECT 1 FROM hadiths WHERE sha256 = ? LIMIT 1', (sha256,))
        return self.cursor.fetchone() is not None
    
    def normalize_hadith_for_db(self, hadith: Dict) -> Dict:
        """
        Normalise un hadith du format connecteur vers le format DB
        """
        # Calculer SHA256
        sha256 = self.calculate_sha256(
            hadith['text_arabic'],
            hadith['collection'],
            hadith['hadith_number']
        )
        
        return {
            'sha256': sha256,
            'collection': hadith['collection'],
            'numero_hadith': hadith['hadith_number'],
            'livre': hadith.get('source_book', ''),
            'chapitre': '',
            'matn_ar': hadith['text_arabic'],
            'matn_fr': '',  # À enrichir plus tard
            'isnad_brut': hadith.get('narrator', ''),
            'grade_final': hadith.get('grade', 'unknown'),
            'categorie': 'hadith',
            'badge_alerte': '',
            'source_url': f"https://api.hadith.gading.dev/{hadith['collection_id']}/{hadith['hadith_number']}",
            'source_api': hadith['source_api'],
            'inserted_at': datetime.utcnow().isoformat()
        }
    
    def insert_hadith(self, hadith: Dict) -> bool:
        """
        Insère un hadith dans la base
        
        Returns:
            True si inséré, False si doublon
        """
        # Normaliser pour la DB
        db_hadith = self.normalize_hadith_for_db(hadith)
        
        # Vérifier doublon
        if self.hadith_exists(db_hadith['sha256']):
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
                db_hadith['sha256'],
                db_hadith['collection'],
                db_hadith['numero_hadith'],
                db_hadith['livre'],
                db_hadith['chapitre'],
                db_hadith['matn_ar'],
                db_hadith['matn_fr'],
                db_hadith['isnad_brut'],
                db_hadith['grade_final'],
                db_hadith['categorie'],
                db_hadith['badge_alerte'],
                db_hadith['source_url'],
                db_hadith['source_api'],
                db_hadith['inserted_at']
            ))
            
            self.stats['total_imported'] += 1
            
            # Compter par source et collection
            source = db_hadith['source_api']
            collection = db_hadith['collection']
            
            self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
            self.stats['by_collection'][collection] = self.stats['by_collection'].get(collection, 0) + 1
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur insertion: {e}")
            self.stats['errors'] += 1
            return False
    
    def harvest_hadith_gading_collections(self):
        """
        Harveste les collections manquantes de hadith-gading.com
        """
        print("\n" + "="*80)
        print("📚 HARVESTING HADITH-GADING.COM")
        print("="*80)
        
        # Collections prioritaires (Kutub al-Sittah manquants)
        collections = [
            ('tirmidzi', 4000),   # Jami' at-Tirmidhi
            ('nasai', 5800),      # Sunan an-Nasa'i
            ('ahmad', 27000),     # Musnad Ahmad (partiel)
            ('malik', 2000),      # Muwatta Malik
        ]
        
        for book_id, max_hadiths in collections:
            print(f"\n📖 Collection: {book_id}")
            print(f"   Objectif: {max_hadiths:,} hadiths")
            
            try:
                # Harvester par batches de 100
                hadiths = self.hadith_gading.harvest_collection(
                    book=book_id,
                    max_hadiths=max_hadiths,
                    batch_size=100
                )
                
                if not hadiths:
                    print(f"⚠️  Aucun hadith récupéré pour {book_id}")
                    continue
                
                # Insertion
                imported = 0
                for hadith in hadiths:
                    if self.insert_hadith(hadith):
                        imported += 1
                        if imported % 500 == 0:
                            self.conn.commit()
                            print(f"   💾 {imported:,} hadiths importés...")
                
                self.conn.commit()
                print(f"✅ {book_id}: {imported:,} hadiths importés")
                
                # Pause entre collections
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur {book_id}: {e}")
                import traceback
                traceback.print_exc()
    
    def harvest_jsdelivr_collections(self):
        """
        Harveste les collections depuis JSDelivr CDN
        """
        print("\n" + "="*80)
        print("📦 HARVESTING JSDELIVR CDN")
        print("="*80)
        
        # Collections arabes disponibles
        editions = [
            'ara-tirmidzi',
            'ara-nasai',
            'ara-malik',
            'ara-abudawud'
        ]
        
        for edition in editions:
            print(f"\n📥 Téléchargement: {edition}")
            
            try:
                hadiths = self.jsdelivr.get_full_collection(edition)
                
                if not hadiths:
                    print(f"⚠️  Aucun hadith récupéré pour {edition}")
                    continue
                
                # Insertion
                imported = 0
                for hadith in hadiths:
                    if self.insert_hadith(hadith):
                        imported += 1
                        if imported % 500 == 0:
                            self.conn.commit()
                            print(f"   💾 {imported:,} hadiths importés...")
                
                self.conn.commit()
                print(f"✅ {edition}: {imported:,} hadiths importés")
                
                # Pause entre collections
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur {edition}: {e}")
                import traceback
                traceback.print_exc()
    
    def print_final_report(self):
        """Affiche le rapport final"""
        print("\n" + "="*80)
        print("📊 RAPPORT FINAL")
        print("="*80)
        
        current_count = self.get_current_count()
        
        print(f"\n📈 Statistiques globales:")
        print(f"   Total en base: {current_count:,} hadiths")
        print(f"   Importés: {self.stats['total_imported']:,}")
        print(f"   Doublons évités: {self.stats['duplicates_skipped']:,}")
        print(f"   Erreurs: {self.stats['errors']}")
        
        print(f"\n📚 Par collection:")
        for collection, count in sorted(self.stats['by_collection'].items()):
            print(f"   {collection}: {count:,} hadiths")
        
        print(f"\n🔌 Par source API:")
        for source, count in sorted(self.stats['by_source'].items()):
            print(f"   {source}: {count:,} hadiths")
        
        # Progression vers objectif
        target = 150000
        progress = (current_count / target) * 100
        remaining = target - current_count
        
        print(f"\n🎯 Progression vers 150K:")
        print(f"   Actuel: {current_count:,} / {target:,} ({progress:.1f}%)")
        print(f"   Restant: {remaining:,} hadiths")
        
        # Barre de progression
        bar_length = 50
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"   [{bar}] {progress:.1f}%")
    
    def run(self):
        """Lance le harvesting complet"""
        print("="*80)
        print("🚀 DÉMARRAGE HARVESTING PHASE 2")
        print("="*80)
        
        start_time = time.time()
        initial_count = self.get_current_count()
        
        print(f"\n📊 État initial: {initial_count:,} hadiths")
        
        # Phase 1: Hadith Gading
        try:
            self.harvest_hadith_gading_collections()
        except Exception as e:
            print(f"\n❌ Erreur Phase Hadith Gading: {e}")
        
        # Phase 2: JSDelivr CDN
        try:
            self.harvest_jsdelivr_collections()
        except Exception as e:
            print(f"\n❌ Erreur Phase JSDelivr: {e}")
        
        # Rapport final
        elapsed = time.time() - start_time
        print(f"\n⏱️  Temps total: {elapsed/60:.1f} minutes")
        
        self.print_final_report()
        
        # Fermeture
        self.conn.close()
        
        print("\n" + "="*80)
        print("✅ HARVESTING TERMINÉ")
        print("="*80)

def main():
    """Point d'entrée principal"""
    harvester = FixedHarvester()
    harvester.run()

if __name__ == "__main__":
    main()