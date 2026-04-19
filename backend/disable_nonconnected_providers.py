import sqlite3

DB_PATH = r'C:\\Users\\sabri\\.omniroute\\storage.sqlite'
KEEP = {'kiro', 'groq', 'gemini', 'serper-search'}

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT DISTINCT provider FROM provider_connections')
    allp = [p[0] for p in c.fetchall()]
    disabled = []
    for p in allp:
        if p not in KEEP:
            c.execute(
                'INSERT OR REPLACE INTO disabled_providers (provider_name, reason, disabled_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                (p, 'Non connecté ou non autorisé')
            )
            disabled.append(p)
    conn.commit()
    print('Providers désactivés :', disabled)
    conn.close()

if __name__ == '__main__':
    main()