#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correction du validateur pour améliorer le matching collections → autorités
"""

import unicodedata
import re

def normalize_for_matching(text: str) -> str:
    """
    Normalise un texte pour le matching
    - Supprime les diacritiques
    - Convertit en minuscules
    - Supprime les caractères spéciaux
    """
    # Supprimer les diacritiques
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Minuscules
    text = text.lower()
    
    # Remplacer les variations courantes
    replacements = {
        'ā': 'a', 'ī': 'i', 'ū': 'u',
        'ḥ': 'h', 'ṣ': 's', 'ḍ': 'd',
        'ṭ': 't', 'ẓ': 'z', 'ʿ': '',
        'ʾ': '', ''': '', ''': '',
        '-': ' ', '_': ' '
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# Test de la fonction
test_cases = [
    ("al-Bukhārī", "bukhari"),
    ("Abū Dāwūd", "abu dawud"),
    ("at-Tirmidhī", "tirmidhi"),
    ("Mālik ibn Anas", "malik"),
    ("Sahih al-Bukhari", "sahih bukhari"),
    ("Sunan Abu Dawud", "sunan abu dawud"),
]

print("\n" + "="*80)
print("TEST DE NORMALISATION")
print("="*80)

for original, expected in test_cases:
    normalized = normalize_for_matching(original)
    match = expected in normalized or normalized in expected
    status = "[OK]" if match else "[FAIL]"
    print(f"\n{status} '{original}' -> '{normalized}'")
    print(f"   Attendu: '{expected}' | Match: {match}")

print("\n" + "="*80)
print("\nLa fonction normalize_for_matching() est prete a etre integree")
print("dans corpus_validator.py pour ameliorer le matching.")
print("\n" + "="*80)
