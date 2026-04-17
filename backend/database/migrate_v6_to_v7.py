#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migration AL-MĪZĀN V6.0 → V7.0
Migre les données existantes vers le nouveau schéma
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationV6toV7:
    """Gestionnaire de migration V6 → V7"""
    
    def __init__(self, v6_db_path: str = "backend/database/almizan.db",
                 v7_db_path: str = "backend/database/almizan_v7.db"):
        # Utiliser des chemins absolus depuis la racine du projet
        project_root = Path(__file__).parent.parent.parent
        self.v6_db_path = project_root / v6_db_path
        self.v7_db_path = project_root / v7_db_path
        self.schema_v7_path = project_root / "backend/database/schema_v7.sql"
        
    def create_v7_database(self):
        """Créer la nouvelle base de données V7"""
        logger.info("Création de la base de données V7...")
        
        # Lire le schéma V7
        with open(self.schema_v7_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Créer la base V7
        conn = sqlite3.connect(self.v7_db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Base de données V7 créée: {self.v7_db_path}")
    
    def migrate_entries(self):
        """Migrer les entrées de V6 vers V7"""
        logger.info("Migration des entrées V6 → V7...")
        
        # Connexion aux deux bases
        conn_v6 = sqlite3.connect(self.v6_db_path)
        conn_v6.row_factory = sqlite3.Row
        conn_v7 = sqlite3.connect(self.v7_db_path)
        
        # Récupérer toutes les entrées V6
        cursor_v6 = conn_v6.execute("SELECT * FROM entries")
        entries_v6 = cursor_v6.fetchall()
        
        migrated_count = 0
        error_count = 0
        
        for entry_v6 in entries_v6:
            try:
                # Mapper V6 → V7
                entry_v7 = self._map_entry_v6_to_v7(dict(entry_v6))
                
                # Insérer dans V7
                conn_v7.execute("""
                    INSERT INTO entries (
                        id, zone_id, zone_label,
                        ar_text, ar_text_clean, ar_narrator,
                        fr_text, fr_summary, fr_source,
                        grade_primary, grade_by_mohdith,
                        book_name_ar, book_name_fr, hadith_number,
                        source_api, source_url, source_data_license,
                        created_at, updated_at, verified_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_v7['id'],
                    entry_v7['zone_id'],
                    entry_v7['zone_label'],
                    entry_v7['ar_text'],
                    entry_v7['ar_text_clean'],
                    entry_v7.get('ar_narrator'),
                    entry_v7.get('fr_text'),
                    entry_v7.get('fr_summary'),
                    entry_v7.get('fr_source', 'none'),
                    entry_v7.get('grade_primary', 'unknown'),
                    entry_v7.get('grade_by_mohdith'),
                    entry_v7.get('book_name_ar'),
                    entry_v7.get('book_name_fr'),
                    entry_v7.get('hadith_number'),
                    entry_v7.get('source_api', 'manual'),
                    entry_v7.get('source_url'),
                    entry_v7.get('source_data_license', 'unknown'),
                    entry_v7.get('created_at'),
                    entry_v7.get('updated_at'),
                    entry_v7.get('verified_by', 'system')
                ))
                
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Erreur migration entrée {entry_v6['id']}: {e}")
                error_count += 1
        
        conn_v7.commit()
        conn_v6.close()
        conn_v7.close()
        
        logger.info(f"✅ Migration terminée: {migrated_count} entrées migrées, {error_count} erreurs")
    
    def _map_entry_v6_to_v7(self, entry_v6: Dict[str, Any]) -> Dict[str, Any]:
        """Mapper une entrée V6 vers le format V7"""
        
        # Nettoyer le texte arabe (retirer tashkîl pour recherche)
        ar_text_clean = self._remove_tashkil(entry_v6.get('arabic_text', ''))
        
        # Mapper le grade V6 → V7
        grade_mapping = {
            'sahih': 'Sahih',
            'hasan': 'Hasan',
            'daif': 'Da\'if',
            'mawdu': 'Mawdu\'',
            'munkar': 'Munkar'
        }
        grade_primary = grade_mapping.get(entry_v6.get('grading', '').lower(), 'unknown')
        
        # Obtenir le label de zone
        zone_label = self._get_zone_label(entry_v6['zone_id'])
        
        return {
            'id': entry_v6['id'],
            'zone_id': entry_v6['zone_id'],
            'zone_label': zone_label,
            'ar_text': entry_v6.get('arabic_text', ''),
            'ar_text_clean': ar_text_clean,
            'ar_narrator': None,  # À enrichir plus tard
            'fr_text': entry_v6.get('english_text'),  # Temporaire
            'fr_summary': entry_v6.get('fr_summary'),
            'fr_source': 'manual',
            'grade_primary': grade_primary,
            'grade_by_mohdith': entry_v6.get('grader'),
            'book_name_ar': entry_v6.get('book_name'),
            'book_name_fr': entry_v6.get('book_name'),
            'hadith_number': entry_v6.get('hadith_number'),
            'source_api': 'manual',
            'source_url': entry_v6.get('source_reference'),
            'source_data_license': 'unknown',
            'created_at': entry_v6.get('created_at'),
            'updated_at': entry_v6.get('updated_at'),
            'verified_by': 'system'
        }
    
    def _remove_tashkil(self, text: str) -> str:
        """Retirer les diacritiques arabes pour la recherche"""
        import re
        # Caractères diacritiques arabes
        tashkil_pattern = re.compile(r'[\u064B-\u065F\u0670]')
        return tashkil_pattern.sub('', text)
    
    def _get_zone_label(self, zone_id: int) -> str:
        """Obtenir le label d'une zone"""
        zone_labels = {
            1: 'Isnad', 2: 'Matn', 3: 'Tarjîh', 4: 'Takhrîj', 5: 'Ilal',
            6: 'Shurûh', 7: 'Naskh', 8: 'Mukhtalif al-Hadith', 9: 'Qawâ\'id', 10: 'Rijal',
            11: 'Grading', 12: 'Sahîh', 13: 'Hasan', 14: 'Da\'îf', 15: 'Mawdû\'',
            16: 'Mutawâtir', 17: 'Âhâd', 18: 'Mursal / Munqati\'', 19: 'Musnad Ahmad', 20: 'Silsilah Al-Albânî',
            21: 'Aqîdah', 22: 'Fiqh al-\'Ibâdât', 23: 'Mu\'âmalât', 24: 'Hadith Qudsî', 25: 'Âthâr as-Sahâbah',
            26: 'Nawâhî', 27: 'Fadâ\'il', 28: 'Dhikr et Du\'â\'', 29: 'Zuhd et Raqâ\'iq', 30: 'Fatâwâ Salafiyyah',
            31: 'Manâqib et Sîrah', 32: 'Hadith Fabricado'
        }
        return zone_labels.get(zone_id, f'Zone {zone_id}')
    
    def verify_migration(self):
        """Vérifier l'intégrité de la migration"""
        logger.info("Vérification de la migration...")
        
        conn_v6 = sqlite3.connect(self.v6_db_path)
        conn_v7 = sqlite3.connect(self.v7_db_path)
        
        # Compter les entrées
        count_v6 = conn_v6.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        count_v7 = conn_v7.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        
        logger.info(f"Entrées V6: {count_v6}")
        logger.info(f"Entrées V7: {count_v7}")
        
        if count_v6 == count_v7:
            logger.info("✅ Migration vérifiée: tous les enregistrements ont été migrés")
        else:
            logger.warning(f"⚠️  Différence détectée: {count_v6 - count_v7} entrées manquantes")
        
        # Vérifier les zones
        zones_v7 = conn_v7.execute("SELECT COUNT(*) FROM zones").fetchone()[0]
        logger.info(f"Zones V7: {zones_v7}/32")
        
        conn_v6.close()
        conn_v7.close()
    
    def run_full_migration(self):
        """Exécuter la migration complète"""
        logger.info("=== DÉBUT MIGRATION V6.0 → V7.0 ===\n")
        
        # Vérifier que V6 existe
        if not Path(self.v6_db_path).exists():
            logger.warning(f"Base V6 introuvable: {self.v6_db_path}")
            logger.info("Création d'une nouvelle base V7 vide...")
            self.create_v7_database()
            return
        
        # Créer V7
        self.create_v7_database()
        
        # Migrer les données
        self.migrate_entries()
        
        # Vérifier
        self.verify_migration()
        
        logger.info("\n=== MIGRATION TERMINÉE ===")
        logger.info(f"Nouvelle base de données: {self.v7_db_path}")

def main():
    """Point d'entrée principal"""
    migration = MigrationV6toV7()
    migration.run_full_migration()

if __name__ == '__main__':
    main()