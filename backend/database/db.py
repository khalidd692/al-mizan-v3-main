"""
Configuration base de données - Point central pour DB_PATH
"""
import os
from pathlib import Path

# Détection auto du chemin DB
DB_PATH = Path(os.environ.get(
    "DATABASE_URL", "sqlite:///backend/database/almizan_v7.db"
).replace("sqlite:///", "").replace("sqlite://", ""))
