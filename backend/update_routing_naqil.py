import sqlite3
import json
import datetime

DB_PATH = r'C:\\Users\\sabri\\.omniroute\\storage.sqlite'

# Routing Naqil strict pour Al Mizân (tâches A-F)
TASKS = [
    {
        "task_id": "A",
        "task_name": "Reformulation requête utilisateur",
        "description": "FR mal écrit → requête propre",
        "config": {
            "model": "groq/llama-3.3-70b-versatile",
            "temperature": 0.2,
            "max_tokens": 300,
            "timeout": 8,
            "fallback": "gemini/gemini-2.0-flash"
        }
    },
    {
        "task_id": "B",
        "task_name": "Traduction AR→FR d'appoint",
        "description": "Traduction automatique - non validée par scholar",
        "config": {
            "model": "kiro/claude-sonnet-4.5",
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout": 25,
            "fallback": "groq/qwen3-32b"
        }
    },
    {
        "task_id": "C",
        "task_name": "Parsing JSON Dorar/Sahab API",
        "description": "Parsing JSON Dorar/Sahab API",
        "config": {
            "model": "groq/llama-3.3-70b-versatile",
            "temperature": 0.0,
            "max_tokens": 1500,
            "timeout": 10,
            "fallback": "kiro/claude-haiku-4.5"
        }
    },
    {
        "task_id": "D",
        "task_name": "Résumé réponse pour UI",
        "description": "Résumé réponse pour affichage UI",
        "config": {
            "model": "kiro/claude-haiku-4.5",
            "temperature": 0.2,
            "max_tokens": 600,
            "timeout": 10,
            "fallback": "groq/llama-3.3-70b-versatile"
        }
    },
    {
        "task_id": "E",
        "task_name": "Classification intention",
        "description": "Classification intention (quel onglet router)",
        "config": {
            "model": "groq/llama-3.3-70b-versatile",
            "temperature": 0.0,
            "max_tokens": 100,
            "timeout": 5
        }
    },
    {
        "task_id": "F",
        "task_name": "Recherche web (hadith non trouvé en local)",
        "description": "serper search → résumé par groq/llama-3.3-70b",
        "config": {
            "model": "serper-search + groq/llama-3.3-70b-versatile",
            "note": "toujours afficher la source et 'source externe non vérifiée'"
        }
    }
]

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat()
    for t in TASKS:
        c.execute(
            '''INSERT OR REPLACE INTO routing_config
               (task_id, task_name, description, config_json, updated_at)
               VALUES (?, ?, ?, ?, ?)''',
            (
                t["task_id"],
                t["task_name"],
                t["description"],
                json.dumps(t["config"], ensure_ascii=False),
                now
            )
        )
        # print supprimé pour éviter UnicodeEncodeError sur Windows console
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()