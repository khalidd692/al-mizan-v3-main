import sqlite3
import os

db_path = 'corpus/corpus.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables trouvées: {tables if tables else 'AUCUNE'}")
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} entrées")
    
    conn.close()
else:
    print(f"Base de données non trouvée: {db_path}")