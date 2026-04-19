#!/usr/bin/env python3
"""
Import des datasets de hadiths depuis GitHub
- 40 Hadiths de Nawawi depuis osamayy/40-hadith-nawawi-db
- Autres datasets disponibles
"""

import sqlite3
import json
import hashlib
import requests
from typing import List, Dict
import time

class GitHubHadithImporter:
    """Importe les hadiths depuis les repos GitHub"""
    
    def __init__(self, db_path: str = 'almizane.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connexion à la base de données"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✅ Connecté à {self.db_path}")
    
    def close(self):
        """Fermeture de la connexion"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")
    
    def generate_hash(self, matn_ar: str) -> str:
        """Génère un hash SHA256 du matn arabe"""
        return hashlib.sha256(matn_ar.encode('utf-8')).hexdigest()
    
    def hadith_exists(self, sha256: str) -> bool:
        """Vérifie si un hadith existe déjà"""
        self.cursor.execute("SELECT id FROM hadiths WHERE sha256 = ?", (sha256,))
        return self.cursor.fetchone() is not None
    
    def import_nawawi_40(self):
        """
        Importe les 40 Hadiths de Nawawi depuis GitHub
        Source: https://github.com/osamayy/40-hadith-nawawi-db
        """
        print("\n📚 Import des 40 Hadiths de Nawawi...")
        print("-" * 60)
        
        # URL du fichier JSON sur GitHub
        url = "https://raw.githubusercontent.com/osamayy/40-hadith-nawawi-db/main/40-hadith-nawawi.json"
        
        try:
            # Télécharger le fichier
            print(f"📥 Téléchargement depuis {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ {len(data)} hadiths téléchargés")
            
            # Importer les hadiths
            imported = 0
            duplicates = 0
            errors = 0
            
            for idx, item in enumerate(data, 1):
                try:
                    # Extraire les données
                    hadith_text = item.get('hadith', '')
                    description = item.get('description', '')
                    
                    # Le matn est dans le champ 'hadith'
                    matn_ar = hadith_text
                    
                    # Générer le hash
                    sha256 = self.generate_hash(matn_ar)
                    
                    # Vérifier les doublons
                    if self.hadith_exists(sha256):
                        duplicates += 1
                        continue
                    
                    # Insérer dans la base
                    self.cursor.execute("""
                        INSERT INTO hadiths (
                            collection, numero_hadith, matn_ar, 
                            grade_final, categorie, sha256, source_api
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'forty_hadith_nawawi',
                        str(idx),
                        matn_ar,
                        'sahih',  # Les 40 hadiths de Nawawi sont authentiques
                        'MAQBUL',  # Catégorie pour hadiths authentiques
                        sha256,
                        'github:osamayy/40-hadith-nawawi-db'
                    ))
                    
                    imported += 1
                    
                    if idx % 10 == 0:
                        print(f"✅ {idx}/{len(data)} hadiths traités")
                        self.conn.commit()
                
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur hadith {idx}: {e}")
            
            # Commit final
            self.conn.commit()
            
            print(f"\n✅ Import terminé !")
            print(f"   - Importés : {imported}")
            print(f"   - Doublons : {duplicates}")
            print(f"   - Erreurs : {errors}")
            
            return imported
            
        except Exception as e:
            print(f"❌ Erreur lors de l'import : {e}")
            return 0
    
    def import_open_hadith_data(self):
        """
        Importe depuis Open-Hadith-Data
        Source: https://github.com/mhashim6/Open-Hadith-Data
        """
        print("\n📚 Import depuis Open-Hadith-Data...")
        print("-" * 60)
        
        # Liste des collections disponibles
        collections = {
            'bukhari': 'https://raw.githubusercontent.com/mhashim6/Open-Hadith-Data/master/bukhari/bukhari-arabic.csv',
            'muslim': 'https://raw.githubusercontent.com/mhashim6/Open-Hadith-Data/master/muslim/muslim-arabic.csv',
        }
        
        total_imported = 0
        
        for collection_name, url in collections.items():
            print(f"\n📥 Téléchargement de {collection_name}...")
            
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parser le CSV
                lines = response.text.split('\n')
                print(f"✅ {len(lines)} lignes téléchargées")
                
                imported = 0
                duplicates = 0
                
                for line in lines[1:]:  # Skip header
                    if not line.strip():
                        continue
                    
                    try:
                        # Format CSV: hadith_number,hadith_text
                        parts = line.split(',', 1)
                        if len(parts) < 2:
                            continue
                        
                        numero = parts[0].strip()
                        matn_ar = parts[1].strip().strip('"')
                        
                        # Générer le hash
                        sha256 = self.generate_hash(matn_ar)
                        
                        # Vérifier les doublons
                        if self.hadith_exists(sha256):
                            duplicates += 1
                            continue
                        
                        # Insérer
                        self.cursor.execute("""
                            INSERT INTO hadiths (
                                collection, numero_hadith, matn_ar,
                                sha256, source_api
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            f'sahih_{collection_name}',
                            numero,
                            matn_ar,
                            sha256,
                            'github:mhashim6/Open-Hadith-Data'
                        ))
                        
                        imported += 1
                        
                        if imported % 100 == 0:
                            print(f"✅ {imported} hadiths importés...")
                            self.conn.commit()
                    
                    except Exception as e:
                        continue
                
                self.conn.commit()
                total_imported += imported
                
                print(f"✅ {collection_name} : {imported} importés, {duplicates} doublons")
            
            except Exception as e:
                print(f"❌ Erreur {collection_name}: {e}")
        
        return total_imported

def main():
    """Point d'entrée principal"""
    importer = GitHubHadithImporter()
    
    try:
        importer.connect()
        
        # Import des 40 Hadiths de Nawawi
        nawawi_count = importer.import_nawawi_40()
        
        print(f"\n{'='*60}")
        print(f"📊 RÉSUMÉ FINAL")
        print(f"{'='*60}")
        print(f"Total importé : {nawawi_count} hadiths")
        print(f"{'='*60}")
        
    finally:
        importer.close()

if __name__ == '__main__':
    main()