#!/usr/bin/env python3
"""
Script de test rapide pour valider l'environnement avant l'import massif
"""

import sys
import subprocess
import sqlite3
from pathlib import Path

def test_python_version():
    """Vérifie la version Python"""
    print("🔍 Test 1: Version Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (requis: 3.8+)")
        return False

def test_git():
    """Vérifie Git"""
    print("🔍 Test 2: Git...")
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("   ❌ Git non trouvé")
        return False
    return False

def test_aiohttp():
    """Vérifie aiohttp"""
    print("🔍 Test 3: Module aiohttp...")
    try:
        import aiohttp
        print(f"   ✅ aiohttp {aiohttp.__version__}")
        return True
    except ImportError:
        print("   ❌ aiohttp non installé")
        print("   💡 Installer avec: pip install aiohttp")
        return False

def test_database():
    """Vérifie la base de données"""
    print("🔍 Test 4: Base de données...")
    db_path = Path("backend/almizane.db")
    
    if not db_path.exists():
        print("   ⚠️  Base de données non trouvée")
        print("   💡 Elle sera créée automatiquement lors de l'import")
        return True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'hadiths' in tables:
            count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
            print(f"   ✅ Base existante: {count:,} hadiths")
        else:
            print("   ⚠️  Table 'hadiths' manquante")
            print("   💡 Elle sera créée automatiquement")
        
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_corpus_dir():
    """Vérifie le dossier corpus"""
    print("🔍 Test 5: Dossier corpus...")
    corpus_dir = Path("corpus")
    
    if not corpus_dir.exists():
        print("   ⚠️  Dossier 'corpus' non trouvé")
        print("   💡 Il sera créé automatiquement")
        return True
    
    sunnah_dir = corpus_dir / "sunnah-com"
    if sunnah_dir.exists():
        json_files = list(sunnah_dir.glob("**/*.json"))
        print(f"   ✅ Sunnah.com déjà cloné ({len(json_files)} fichiers)")
    else:
        print("   ℹ️  Sunnah.com pas encore cloné")
        print("   💡 Sera cloné lors du premier import")
    
    return True

def test_mass_importer():
    """Vérifie le script d'import"""
    print("🔍 Test 6: Script mass_importer.py...")
    script_path = Path("backend/mass_importer.py")
    
    if not script_path.exists():
        print("   ❌ Script non trouvé")
        return False
    
    print("   ✅ Script présent")
    return True

def test_internet():
    """Vérifie la connexion Internet"""
    print("🔍 Test 7: Connexion Internet...")
    try:
        import urllib.request
        urllib.request.urlopen('https://github.com', timeout=5)
        print("   ✅ Connexion active")
        return True
    except:
        print("   ❌ Pas de connexion")
        print("   💡 Connexion requise pour cloner les repos")
        return False

def main():
    """Lance tous les tests"""
    print("=" * 60)
    print("🧪 TEST ENVIRONNEMENT - SOLUTION GRATUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_python_version,
        test_git,
        test_aiohttp,
        test_database,
        test_corpus_dir,
        test_mass_importer,
        test_internet
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print()
        print("🚀 PRÊT POUR L'IMPORT !")
        print()
        print("Commandes suggérées:")
        print("  1. Import rapide (50K, ~20 min):")
        print("     python backend/mass_importer.py --source sunnah_com")
        print()
        print("  2. Import complet (125K, ~2-3h):")
        print("     python backend/mass_importer.py --source all")
    else:
        print(f"⚠️  {total - passed} test(s) échoué(s)")
        print()
        print("💡 Corrigez les problèmes avant de lancer l'import")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)