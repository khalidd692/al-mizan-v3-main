"""
Vérifier les verdicts Dorar ajoutés
"""
import sqlite3
from pathlib import Path

DB = Path("backend/almizane.db")
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("="*60)
print("VÉRIFICATION DES VERDICTS DORAR")
print("="*60)

# Compter les verdicts
cur.execute("SELECT COUNT(*) as total FROM ahkam")
total = cur.fetchone()['total']
print(f"\n✓ Total verdicts dans ahkam : {total}")

# Compter par source
cur.execute("""
  SELECT s.name_ar, COUNT(*) as nb
  FROM ahkam a
  JOIN hukm_sources s ON s.id = a.source_id
  GROUP BY s.name_ar
  ORDER BY nb DESC
  LIMIT 10
""")
print("\n📊 Top 10 sources :")
for row in cur.fetchall():
    print(f"  • {row['name_ar']}: {row['nb']} verdicts")

# Compter par classe de hukm
cur.execute("""
  SELECT hukm_class, COUNT(*) as nb
  FROM ahkam
  GROUP BY hukm_class
  ORDER BY nb DESC
""")
print("\n📊 Répartition par classe :")
for row in cur.fetchall():
    print(f"  • {row['hukm_class']}: {row['nb']}")

# Exemples de verdicts
cur.execute("""
  SELECT h.id, h.collection, h.numero_hadith, 
         s.name_ar as muhaddith, a.hukm_class, a.hukm_raw_ar
  FROM ahkam a
  JOIN hadiths h ON h.id = a.hadith_id
  JOIN hukm_sources s ON s.id = a.source_id
  WHERE a.scraped_from = 'dorar.net'
  LIMIT 5
""")
print("\n📝 Exemples de verdicts :")
for row in cur.fetchall():
    print(f"\n  Hadith #{row['id']} ({row['collection']} {row['numero_hadith']})")
    print(f"    Muhaddith: {row['muhaddith']}")
    print(f"    Classe: {row['hukm_class']}")
    print(f"    Verdict: {row['hukm_raw_ar'][:80]}...")

conn.close()
print("\n" + "="*60)