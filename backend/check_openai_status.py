#!/usr/bin/env python3
"""
Script pour vérifier si le provider OpenAI est désactivé dans OmniRoute
"""

import sqlite3

DB_PATH = r'C:\\Users\\sabri\\.omniroute\\storage.sqlite'

def check_openai_status():
    """Vérifie si OpenAI est désactivé dans la base de données OmniRoute."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Vérifier si OpenAI est désactivé
        c.execute('SELECT provider_name FROM disabled_providers WHERE provider_name = ?', ('openai',))
        result = c.fetchone()

        if result:
            print("OpenAI est DEJA desactive dans OmniRoute.")
            return True
        else:
            print("OpenAI n'est PAS encore desactive dans OmniRoute.")
            return False

    except sqlite3.Error as e:
        print(f"Erreur SQLite: {e}")
        return False
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_openai_status()