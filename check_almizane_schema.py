import sqlite3

conn = sqlite3.connect("backend/almizane.db")
cur = conn.cursor()

# Lister toutes les tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print("Tables disponibles:")
for t in tables:
    print(f"  - {t}")

# Schéma de la table hadiths
print("\n" + "="*60)
print("Schéma de la table 'hadiths':")
print("="*60)
cur.execute("PRAGMA table_info(hadiths)")
for row in cur.fetchall():
    print(f"  {row[1]:30} {row[2]:15} {'NOT NULL' if row[3] else ''}")

# Compter les hadiths
cur.execute("SELECT COUNT(*) FROM hadiths")
count = cur.fetchone()[0]
print(f"\nNombre total de hadiths: {count:,}")

conn.close()