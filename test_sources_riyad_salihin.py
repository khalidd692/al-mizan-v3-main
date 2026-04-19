#!/usr/bin/env python3
"""
Test des sources alternatives pour Riyad al-Salihin
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def test_hadith_gading():
    """Test hadith-gading.com"""
    print("=" * 70)
    print("🧪 TEST HADITH-GADING.COM")
    print("=" * 70)
    print()
    
    try:
        from connectors.hadith_gading_connector import HadithGadingConnector
        
        connector = HadithGadingConnector()
        collections = connector.list_collections()
        
        print(f"✅ Connexion réussie")
        print(f"📚 Collections disponibles: {len(collections)}")
        print()
        
        # Chercher Riyad al-Salihin
        riyad_found = False
        for coll in collections:
            if 'riyad' in coll.lower() or 'salihin' in coll.lower():
                print(f"✅ TROUVÉ: {coll}")
                riyad_found = True
        
        if not riyad_found:
            print("❌ Riyad al-Salihin non trouvé")
            print("\n📋 Collections disponibles:")
            for coll in collections[:20]:
                print(f"   • {coll}")
        
        return riyad_found
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_jsdelivr():
    """Test jsdelivr (GitHub datasets)"""
    print("\n" + "=" * 70)
    print("🧪 TEST JSDELIVR (GITHUB DATASETS)")
    print("=" * 70)
    print()
    
    try:
        from connectors.jsdelivr_connector import JsDelivrConnector
        
        connector = JsDelivrConnector()
        
        # Chercher datasets Riyad al-Salihin
        print("🔍 Recherche de datasets 'riyad salihin'...")
        results = connector.search_hadith_datasets('riyad salihin')
        
        if results:
            print(f"✅ {len(results)} datasets trouvés")
            for result in results[:5]:
                print(f"   • {result}")
            return True
        else:
            print("❌ Aucun dataset trouvé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_dorar():
    """Test dorar.net"""
    print("\n" + "=" * 70)
    print("🧪 TEST DORAR.NET")
    print("=" * 70)
    print()
    
    try:
        import requests
        
        # Test simple de connexion
        url = "https://dorar.net/hadith"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Connexion réussie (status {response.status_code})")
            print(f"📄 Taille réponse: {len(response.text)} caractères")
            
            # Chercher mention de Riyad al-Salihin
            if 'رياض' in response.text or 'الصالحين' in response.text:
                print("✅ Riyad al-Salihin mentionné sur le site")
                return True
            else:
                print("⚠️  Riyad al-Salihin non trouvé dans la page d'accueil")
                return False
        else:
            print(f"❌ Erreur {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Test toutes les sources"""
    print("\n" + "=" * 70)
    print("🔍 RECHERCHE DE SOURCES POUR RIYAD AL-SALIHIN")
    print("=" * 70)
    print()
    
    results = {
        'hadith-gading': test_hadith_gading(),
        'jsdelivr': test_jsdelivr(),
        'dorar': test_dorar()
    }
    
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS")
    print("=" * 70)
    print()
    
    for source, success in results.items():
        status = "✅ Disponible" if success else "❌ Non disponible"
        print(f"{source:20} : {status}")
    
    print()
    
    if any(results.values()):
        print("✅ Au moins une source alternative trouvée")
        print("\n📝 Prochaines étapes:")
        if results['hadith-gading']:
            print("   1. Utiliser hadith-gading.com (priorité)")
        if results['jsdelivr']:
            print("   2. Télécharger datasets GitHub")
        if results['dorar']:
            print("   3. Développer scraper dorar.net")
    else:
        print("❌ Aucune source alternative trouvée")
        print("\n💡 Options:")
        print("   1. Obtenir clé API sunnah.com")
        print("   2. Chercher d'autres sources")
        print("   3. Passer aux autres recueils")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()