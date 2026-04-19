import shutil
from datetime import datetime
from pathlib import Path

# Créer le dossier backups s'il n'existe pas
backups_dir = Path("backups")
backups_dir.mkdir(exist_ok=True)

# Générer le nom du backup avec timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
source = Path("backend/almizane.db")
backup = backups_dir / f"almizane_{timestamp}.db"

# Copier
print(f"Backup de {source} vers {backup}...")
shutil.copy2(source, backup)
print(f"✅ Backup créé : {backup}")
print(f"   Taille : {backup.stat().st_size / 1024 / 1024:.1f} MB")