"""Centralise le chemin de la base de données SQLite Al-Mīzān."""
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "almizan_v7.db")
