"""
Debug du parser Dorar - voir ce qui est extrait
"""
from pathlib import Path
from bs4 import BeautifulSoup

cache_file = Path("backend/cache/dorar/09f7ec3722270247.html")
html = cache_file.read_text(encoding='utf-8')

soup = BeautifulSoup(html, 'html.parser')

# Trouver tous les blocs
hadith_divs = soup.find_all('div', class_='hadith')
info_divs = soup.find_all('div', class_='hadith-info')

print(f"Trouvé {len(hadith_divs)} hadiths et {len(info_divs)} info blocks\n")

# Analyser le premier bloc
if info_divs:
    info_div = info_divs[0]
    print("="*60)
    print("PREMIER BLOC INFO (méthode get_text avec séparateur):")
    print("="*60)
    info_text = info_div.get_text(separator='|', strip=True)
    print(info_text)
    print("\n" + "="*60)
    print("LIGNES SPLITÉES:")
    print("="*60)
    lines = [l.strip() for l in info_text.split('|') if l.strip()]
    for i, line in enumerate(lines):
        print(f"{i}: {line}")
    
    print("\n" + "="*60)
    print("RECHERCHE DES CLÉS:")
    print("="*60)
    for i, line in enumerate(lines):
        if 'الراوي:' in line:
            print(f"✓ Trouvé 'الراوي:' à la ligne {i}")
            if i+1 < len(lines):
                print(f"  → Valeur: {lines[i+1]}")
        elif 'المحدث:' in line:
            print(f"✓ Trouvé 'المحدث:' à la ligne {i}")
            if i+1 < len(lines):
                print(f"  → Valeur: {lines[i+1]}")
        elif 'المصدر:' in line:
            print(f"✓ Trouvé 'المصدر:' à la ligne {i}")
            if i+1 < len(lines):
                print(f"  → Valeur: {lines[i+1]}")
        elif 'خلاصة حكم المحدث:' in line:
            print(f"✓ Trouvé 'خلاصة حكم المحدث:' à la ligne {i}")
            if i+1 < len(lines):
                print(f"  → Valeur: {lines[i+1]}")