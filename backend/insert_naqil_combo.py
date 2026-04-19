import sqlite3
import uuid
import json
import datetime

DB_PATH = r'C:\\Users\\sabri\\.omniroute\\storage.sqlite'
COMBO_JSON_PATH = 'backend/omniroute_naqil_chain_combo.json'

def main():
    with open(COMBO_JSON_PATH, encoding='utf-8') as f:
        data = json.dumps(json.load(f), ensure_ascii=False)
    now = datetime.datetime.now().isoformat()
    combo_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO combos (id, name, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        (combo_id, 'Al Mizân - Naqil Chain', data, now, now)
    )
    conn.commit()
    print('Combo inséré :', combo_id)
    conn.close()

if __name__ == '__main__':
    main()