#!/usr/bin/env python3
"""
Script pour désactiver spécifiquement le provider OpenAI dans OmniRoute
qui cause des erreurs 503 ALL_ACCOUNTS_INACTIVE.
"""

import sqlite3
import sys

DB_PATH = r'C:\\Users\\sabri\\.omniroute\\storage.sqlite'

def disable_openai_provider():
    """Désactive le provider OpenAI dans la base de données OmniRoute."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Vérifier si OpenAI est déjà désactivé
        c.execute('SELECT provider_name FROM disabled_providers WHERE provider_name = ?', ('openai',))
        if c.fetchone():
            print("✓ Le provider OpenAI est déjà désactivé.")
            return True

        # Désactiver OpenAI
        c.execute(
            'INSERT OR REPLACE INTO disabled_providers (provider_name, reason, disabled_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            ('openai', 'Aucune clé API active - cause ALL_ACCOUNTS_INACTIVE 503')
        )
        conn.commit()

        # Vérifier que la désactivation a bien fonctionné
        c.execute('SELECT provider_name FROM disabled_providers WHERE provider_name = ?', ('openai',))
        if c.fetchone():
            print("✓ Provider OpenAI désactivé avec succès.")
            return True
        else:
            print("✗ Échec de la désactivation du provider OpenAI.")
            return False

    except sqlite3.Error as e:
        print(f"✗ Erreur SQLite: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    success = disable_openai_provider()
    sys.exit(0 if success else 1)