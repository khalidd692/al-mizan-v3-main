#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données AL-MĪZĀN V6.0
Gestion SQLite avec support des 32 zones
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire principal de la base de données"""
    
    def __init__(self, db_path: str = "backend/database/almizan.db"):
        self.db_path = db_path
        self.schema_path = "backend/database/schema.sql"
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Créer la base de données si elle n'existe pas"""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not db_file.exists():
            logger.info(f"Création de la base de données: {self.db_path}")
            self.initialize_schema()
        else:
            logger.info(f"Base de données existante: {self.db_path}")
    
    def initialize_schema(self):
        """Initialiser le schéma de la base de données"""
        schema_file = Path(self.schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schéma SQL introuvable: {self.schema_path}")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        
        logger.info("Schéma de base de données initialisé avec succès")
    
    @contextmanager
    def get_connection(self):
        """Context manager pour les connexions à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_zone_stats(self) -> List[Dict[str, Any]]:
        """Obtenir les statistiques par zone"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM zone_stats ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_zone_by_id(self, zone_id: int) -> Optional[Dict[str, Any]]:
        """Obtenir une zone par son ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM zones WHERE id = ?",
                (zone_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_zones(self) -> List[Dict[str, Any]]:
        """Obtenir toutes les zones"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM zones ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]
    
    def add_source(self, source_data: Dict[str, Any]) -> str:
        """Ajouter une source"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO sources (id, name, url, type, license, last_access, reliability_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_data['id'],
                source_data['name'],
                source_data.get('url'),
                source_data.get('type'),
                source_data.get('license'),
                source_data.get('last_access'),
                source_data.get('reliability_score', 100),
                source_data.get('notes')
            ))
            conn.commit()
        return source_data['id']
    
    def add_entry(self, entry_data: Dict[str, Any]) -> str:
        """Ajouter une entrée (hadith, fatwa, etc.)"""
        with self.get_connection() as conn:
            # Convertir les listes en JSON
            keywords_json = json.dumps(entry_data.get('keywords', []))
            scholarly_tags_json = json.dumps(entry_data.get('scholarly_tags', []))
            
            conn.execute("""
                INSERT INTO entries (
                    id, zone_id, source_id, arabic_text, fr_summary, english_text,
                    source_reference, book_name, chapter_name, hadith_number,
                    keywords, scholarly_tags, grading, grader, grading_source,
                    grading_note, confidence, tawaqquf, tawaqquf_reason,
                    notes, scholarly_commentary, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_data['id'],
                entry_data['zone_id'],
                entry_data['source_id'],
                entry_data.get('arabic_text'),
                entry_data.get('fr_summary'),
                entry_data.get('english_text'),
                entry_data['source_reference'],
                entry_data.get('book_name'),
                entry_data.get('chapter_name'),
                entry_data.get('hadith_number'),
                keywords_json,
                scholarly_tags_json,
                entry_data.get('grading'),
                entry_data.get('grader'),
                entry_data.get('grading_source'),
                entry_data.get('grading_note'),
                entry_data.get('confidence', 50),
                entry_data.get('tawaqquf', False),
                entry_data.get('tawaqquf_reason'),
                entry_data.get('notes'),
                entry_data.get('scholarly_commentary'),
                entry_data.get('version', 'V6.0')
            ))
            conn.commit()
        return entry_data['id']
    
    def get_entries_by_zone(self, zone_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtenir les entrées d'une zone"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT e.*, s.name as source_name, s.url as source_url
                FROM entries e
                JOIN sources s ON e.source_id = s.id
                WHERE e.zone_id = ?
                ORDER BY e.confidence DESC, e.created_at DESC
                LIMIT ?
            """, (zone_id, limit))
            
            entries = []
            for row in cursor.fetchall():
                entry = dict(row)
                # Convertir JSON en listes
                entry['keywords'] = json.loads(entry['keywords']) if entry['keywords'] else []
                entry['scholarly_tags'] = json.loads(entry['scholarly_tags']) if entry['scholarly_tags'] else []
                entries.append(entry)
            
            return entries
    
    def search_entries(self, query: str, zone_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Rechercher des entrées"""
        with self.get_connection() as conn:
            if zone_id:
                cursor = conn.execute("""
                    SELECT e.*, s.name as source_name
                    FROM entries e
                    JOIN sources s ON e.source_id = s.id
                    WHERE e.zone_id = ? AND (
                        e.arabic_text LIKE ? OR
                        e.fr_summary LIKE ? OR
                        e.english_text LIKE ? OR
                        e.keywords LIKE ? OR
                        e.scholarly_tags LIKE ?
                    )
                    ORDER BY e.confidence DESC
                    LIMIT 50
                """, (zone_id, f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            else:
                cursor = conn.execute("""
                    SELECT e.*, s.name as source_name
                    FROM entries e
                    JOIN sources s ON e.source_id = s.id
                    WHERE 
                        e.arabic_text LIKE ? OR
                        e.fr_summary LIKE ? OR
                        e.english_text LIKE ? OR
                        e.keywords LIKE ? OR
                        e.scholarly_tags LIKE ?
                    ORDER BY e.confidence DESC
                    LIMIT 50
                """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            entries = []
            for row in cursor.fetchall():
                entry = dict(row)
                entry['keywords'] = json.loads(entry['keywords']) if entry['keywords'] else []
                entry['scholarly_tags'] = json.loads(entry['scholarly_tags']) if entry['scholarly_tags'] else []
                entries.append(entry)
            
            return entries
    
    def get_coverage_report(self) -> Dict[str, Any]:
        """Générer un rapport de couverture"""
        stats = self.get_zone_stats()
        total_entries = sum(s['entry_count'] for s in stats)
        
        zones_with_data = sum(1 for s in stats if s['entry_count'] > 0)
        coverage_percent = (zones_with_data / 32) * 100
        
        return {
            'total_entries': total_entries,
            'zones_covered': zones_with_data,
            'zones_total': 32,
            'coverage_percent': round(coverage_percent, 2),
            'avg_confidence': round(sum(s['avg_confidence'] or 0 for s in stats) / len(stats), 2),
            'zones': stats
        }
    
    def vacuum(self):
        """Optimiser la base de données"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
        logger.info("Base de données optimisée")

# Instance globale
_db_instance: Optional[DatabaseManager] = None

def get_db() -> DatabaseManager:
    """Obtenir l'instance globale du gestionnaire de base de données"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance