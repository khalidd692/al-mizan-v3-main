#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration OmniRoute pour Al Mizân
Routing intelligent par tâche avec fallbacks optimisés
"""

import sqlite3
import json
import os
import sys
from pathlib import Path

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Chemin vers la base de données OmniRoute
OMNIROUTE_DB = Path.home() / ".omniroute" / "storage.sqlite"

# Configuration de routing par tâche
TASK_ROUTING_CONFIG = {
    "task_1_hadith_verification": {
        "name": "Vérification hadith / analyse isnad",
        "description": "Tâches lourdes nécessitant précision maximale",
        "priorities": [
            {"provider": "kiro", "model": "claude-sonnet-4.5", "priority": 1},
            {"provider": "copilot", "model": "gpt-4.1", "priority": 2},
            {"provider": "groq", "model": "llama-3.3-70b-versatile", "priority": 3},
        ],
        "fallback": {"provider": "groq", "model": "qwen3-32b"}
    },
    "task_2_translation_doctrine": {
        "name": "Traduction FR / Bouclier Doctrinal",
        "description": "Langue + théologie, précision doctrinale",
        "priorities": [
            {"provider": "kiro", "model": "claude-sonnet-4.5", "priority": 1},
            {"provider": "kiro", "model": "claude-haiku-4.5", "priority": 2},
            {"provider": "groq", "model": "qwen3-32b", "priority": 3},
        ],
        "fallback": {"provider": "copilot", "model": "gpt-4o"}
    },
    "task_3_json_parsing": {
        "name": "Parsing JSON / Dorar API / structuration données",
        "description": "Tâches rapides de structuration",
        "priorities": [
            {"provider": "kiro", "model": "claude-haiku-4.5", "priority": 1},
            {"provider": "groq", "model": "llama-3.3-70b-versatile", "priority": 2},
            {"provider": "groq", "model": "gemma-3-27b-it", "priority": 3},
        ],
        "fallback": {"provider": "copilot", "model": "gpt-4.1-mini"}
    },
    "task_4_semantic_search": {
        "name": "Recherche sémantique / classification",
        "description": "Tâches légères de recherche",
        "priorities": [
            {"provider": "groq", "model": "llama-3.3-70b-versatile", "priority": 1},
            {"provider": "groq", "model": "qwen3-32b", "priority": 2},
            {"provider": "kiro", "model": "claude-haiku-4.5", "priority": 3},
        ],
        "fallback": None
    },
    "task_5_universal_fallback": {
        "name": "Fallback universel",
        "description": "Quand tout échoue",
        "priorities": [
            {"provider": "groq", "model": "llama-3.3-70b-versatile", "priority": 1},
            {"provider": "groq", "model": "qwen3-32b", "priority": 2},
            {"provider": "kiro", "model": "claude-haiku-4.5", "priority": 3},
        ],
        "fallback": None
    }
}

# Providers à désactiver
DISABLED_PROVIDERS = ["github", "deepseek", "gemini", "nvidia"]

# Règles globales
GLOBAL_RULES = {
    "timeout_seconds": 15,
    "max_retries": 2,
    "skip_on_402_429": True,
    "no_ai_generation_for_hadith": True
}

def backup_database():
    """Crée une sauvegarde de la base de données"""
    if not OMNIROUTE_DB.exists():
        print(f"❌ Base de données non trouvée : {OMNIROUTE_DB}")
        return False
    
    backup_path = OMNIROUTE_DB.parent / f"storage_backup_{int(os.path.getmtime(OMNIROUTE_DB))}.sqlite"
    import shutil
    shutil.copy2(OMNIROUTE_DB, backup_path)
    print(f"✅ Sauvegarde créée : {backup_path}")
    return True

def read_current_config():
    """Lit la configuration actuelle"""
    if not OMNIROUTE_DB.exists():
        print(f"❌ Base de données non trouvée : {OMNIROUTE_DB}")
        return None
    
    conn = sqlite3.connect(OMNIROUTE_DB)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📋 CONFIGURATION ACTUELLE")
    print("="*80)
    
    # Lire les tables disponibles
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\n📊 Tables disponibles : {[t[0] for t in tables]}")
    
    # Lire la configuration si elle existe
    config_data = {}
    for table_name in [t[0] for t in tables]:
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                config_data[table_name] = {
                    "columns": columns,
                    "sample_rows": len(rows)
                }
                print(f"\n  📁 {table_name}:")
                print(f"     Colonnes: {columns}")
                print(f"     Lignes (échantillon): {len(rows)}")
        except Exception as e:
            print(f"  ⚠️  Erreur lecture {table_name}: {e}")
    
    conn.close()
    return config_data

def apply_configuration():
    """Applique la nouvelle configuration"""
    if not OMNIROUTE_DB.exists():
        print(f"❌ Base de données non trouvée : {OMNIROUTE_DB}")
        return False
    
    conn = sqlite3.connect(OMNIROUTE_DB)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("🔧 APPLICATION DE LA NOUVELLE CONFIGURATION")
    print("="*80)
    
    try:
        # Créer la table de configuration si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routing_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT,
                config_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Créer la table des providers désactivés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS disabled_providers (
                provider_name TEXT PRIMARY KEY,
                reason TEXT,
                disabled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Créer la table des règles globales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_rules (
                rule_key TEXT PRIMARY KEY,
                rule_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insérer les configurations de routing par tâche
        for task_id, config in TASK_ROUTING_CONFIG.items():
            cursor.execute("""
                INSERT OR REPLACE INTO routing_config 
                (task_id, task_name, description, config_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                task_id,
                config["name"],
                config["description"],
                json.dumps(config, ensure_ascii=False)
            ))
            print(f"✅ Tâche configurée : {config['name']}")
        
        # Désactiver les providers
        for provider in DISABLED_PROVIDERS:
            cursor.execute("""
                INSERT OR REPLACE INTO disabled_providers 
                (provider_name, reason, disabled_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (provider, "Quota épuisé ou credentials manquants"))
            print(f"🚫 Provider désactivé : {provider}")
        
        # Appliquer les règles globales
        for rule_key, rule_value in GLOBAL_RULES.items():
            cursor.execute("""
                INSERT OR REPLACE INTO global_rules 
                (rule_key, rule_value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (rule_key, json.dumps(rule_value)))
            print(f"⚙️  Règle globale : {rule_key} = {rule_value}")
        
        conn.commit()
        print("\n✅ Configuration appliquée avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'application : {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def verify_configuration():
    """Vérifie la configuration appliquée"""
    if not OMNIROUTE_DB.exists():
        return False
    
    conn = sqlite3.connect(OMNIROUTE_DB)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("✅ VÉRIFICATION DE LA CONFIGURATION")
    print("="*80)
    
    # Vérifier les tâches
    cursor.execute("SELECT task_id, task_name FROM routing_config ORDER BY task_id")
    tasks = cursor.fetchall()
    print(f"\n📋 Tâches configurées ({len(tasks)}) :")
    for task_id, task_name in tasks:
        print(f"  • {task_id}: {task_name}")
    
    # Vérifier les providers désactivés
    cursor.execute("SELECT provider_name, reason FROM disabled_providers")
    disabled = cursor.fetchall()
    print(f"\n🚫 Providers désactivés ({len(disabled)}) :")
    for provider, reason in disabled:
        print(f"  • {provider}: {reason}")
    
    # Vérifier les règles globales
    cursor.execute("SELECT rule_key, rule_value FROM global_rules")
    rules = cursor.fetchall()
    print(f"\n⚙️  Règles globales ({len(rules)}) :")
    for key, value in rules:
        print(f"  • {key}: {value}")
    
    conn.close()
    return True

def generate_config_summary():
    """Génère un résumé de la configuration"""
    summary = []
    summary.append("\n" + "="*80)
    summary.append("📊 RÉSUMÉ DE LA CONFIGURATION OMNIROUTE POUR AL MIZÂN")
    summary.append("="*80)
    
    summary.append("\n🎯 ROUTING PAR TÂCHE :")
    for task_id, config in TASK_ROUTING_CONFIG.items():
        summary.append(f"\n  {config['name']}")
        summary.append(f"  {'-' * len(config['name'])}")
        for i, prio in enumerate(config["priorities"], 1):
            summary.append(f"  Priorité {i}: {prio['provider']}/{prio['model']}")
        if config.get("fallback"):
            fb = config["fallback"]
            summary.append(f"  Fallback: {fb['provider']}/{fb['model']}")
    
    summary.append("\n\n🚫 PROVIDERS DÉSACTIVÉS :")
    for provider in DISABLED_PROVIDERS:
        summary.append(f"  • {provider}")
    
    summary.append("\n\n⚙️  RÈGLES GLOBALES :")
    for key, value in GLOBAL_RULES.items():
        summary.append(f"  • {key}: {value}")
    
    summary.append("\n" + "="*80)
    
    return "\n".join(summary)

def main():
    """Fonction principale"""
    print("🚀 Configuration OmniRoute pour Al Mizân")
    print("="*80)
    
    # Afficher le résumé de la configuration
    print(generate_config_summary())
    
    # Lire la configuration actuelle
    print("\n📖 Lecture de la configuration actuelle...")
    current_config = read_current_config()
    
    # Créer une sauvegarde
    print("\n💾 Création d'une sauvegarde...")
    if not backup_database():
        print("⚠️  Impossible de créer une sauvegarde, mais on continue...")
    
    # Appliquer la nouvelle configuration
    if apply_configuration():
        # Vérifier la configuration
        verify_configuration()
        
        print("\n" + "="*80)
        print("✅ CONFIGURATION TERMINÉE AVEC SUCCÈS")
        print("="*80)
        print("\n📝 La configuration OmniRoute a été mise à jour.")
        print("🔄 Redémarrez votre IDE pour que les changements prennent effet.")
        return True
    else:
        print("\n❌ Échec de la configuration")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)