#!/usr/bin/env python3
"""Query all distinct grades from the database."""
import sqlite3
from pathlib import Path

DB_PATH = Path('backend/database/almizan_v7.db')
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tables in database:', tables)
print()

# Query on entries table (the main table)
if 'entries' in tables:
    cursor.execute('''
        SELECT grade_albani, COUNT(*) as total 
        FROM entries 
        WHERE grade_albani IS NOT NULL 
        AND grade_albani != '' 
        GROUP BY grade_albani 
        ORDER BY total DESC
    ''')
    results = cursor.fetchall()
    
    print('=== TABLE: entries (grade_albani) ===')
    print(f'{"Grade":<50} | {"Count":>10}')
    print('-' * 65)
    total = 0
    for grade, count in results:
        grade_str = str(grade)[:48] if grade else 'NULL'
        print(f'{grade_str:<50} | {count:>10}')
        total += count
    print('-' * 65)
    print(f'{"TOTAL":<50} | {total:>10}')
    print()
    print(f'Distinct grades count: {len(results)}')

conn.close()
