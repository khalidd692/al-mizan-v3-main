#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lexique de Fer — AL-MĪZĀN V7.0
Traduction contrôlée des Attributs d'Allah
Règle doctrinale NON NÉGOCIABLE
"""

from typing import Dict, List, Tuple
import re

# ============================================================
# LEXIQUE DE FER — Traductions fixes et intouchables
# ============================================================

LEXIQUE_ATTRIBUTS = {
    # Attributs d'action
    'استوى': 'S\'est établi',
    'استوى على العرش': 'S\'est établi sur le Trône',
    'نزل': 'descend',
    'ينزل': 'descend',
    'يأتي': 'vient',
    'أتى': 'est venu',
    'جاء': 'est venu',
    'يجيء': 'vient',
    
    # Attributs essentiels
    'يد الله': 'la Main d\'Allah',
    'يده': 'Sa Main',
    'يدي الله': 'les deux Mains d\'Allah',
    'يديه': 'Ses deux Mains',
    'وجه الله': 'la Face d\'Allah',
    'وجهه': 'Sa Face',
    'عين الله': 'l\'Œil d\'Allah',
    'عينه': 'Son Œil',
    'أعين الله': 'les Yeux d\'Allah',
    
    # Position et élévation
    'فوق': 'au-dessus',
    'العلو': 'l\'élévation',
    'الفوقية': 'le fait d\'être au-dessus',
    'في السماء': 'dans le ciel',
    'على العرش': 'sur le Trône',
    
    # Attributs de sentiment (littéraux)
    'الرحمة': 'la Miséricorde',  # Si attribut d'Allah
    'رحمته': 'Sa Miséricorde',
    'الغضب': 'la Colère',
    'غضبه': 'Sa Colère',
    'المحبة': 'l\'Amour',
    'محبته': 'Son Amour',
    'الحب': 'l\'Amour',
    'حبه': 'Son Amour',
    'الرضا': 'l\'Agrément',
    'رضاه': 'Son Agrément',
    'السخط': 'le Courroux',
    'سخطه': 'Son Courroux',
    
    # Parole divine
    'كلام الله': 'la Parole d\'Allah',
    'كلامه': 'Sa Parole',
    'يتكلم': 'parle',
    'تكلم': 'a parlé',
}

# Termes INTERDITS (ta'wîl)
TERMES_INTERDITS = {
    'puissance': ['يد', 'يده'],  # Ne jamais traduire "Main" par "puissance"
    'essence': ['وجه', 'وجهه'],  # Ne jamais traduire "Face" par "essence"
    'grâce': ['يد', 'رحمة'],
    'se manifeste': ['نزل', 'ينزل'],  # Toujours "descend"
    'au-delà': ['فوق'],  # Toujours "au-dessus"
    's\'élève': ['استوى'],  # Toujours "S'est établi"
    's\'installe': ['استوى'],
}

# ============================================================
# FONCTIONS DE TRADUCTION
# ============================================================

def traduire_avec_lexique(texte_arabe: str) -> str:
    """
    Traduire un texte arabe en appliquant le Lexique de Fer
    
    Args:
        texte_arabe: Texte arabe à traduire
        
    Returns:
        Texte traduit avec Lexique de Fer appliqué
    """
    texte_traduit = texte_arabe
    
    # Appliquer les traductions fixes
    for ar, fr in LEXIQUE_ATTRIBUTS.items():
        # Recherche avec limites de mots pour éviter les faux positifs
        pattern = r'\b' + re.escape(ar) + r'\b'
        texte_traduit = re.sub(pattern, fr, texte_traduit)
    
    return texte_traduit

def verifier_conformite(texte_traduit: str) -> Tuple[bool, List[str]]:
    """
    Vérifier qu'une traduction ne contient pas de termes interdits
    
    Args:
        texte_traduit: Texte français à vérifier
        
    Returns:
        (conforme, liste_erreurs)
    """
    erreurs = []
    
    for terme_interdit, contextes_ar in TERMES_INTERDITS.items():
        if terme_interdit.lower() in texte_traduit.lower():
            erreurs.append(
                f"⚠️ Terme interdit détecté: '{terme_interdit}' "
                f"(contexte arabe: {', '.join(contextes_ar)})"
            )
    
    return len(erreurs) == 0, erreurs

def get_prompt_lexique_fer() -> str:
    """
    Obtenir le prompt complet du Lexique de Fer pour Claude/LLM
    
    Returns:
        Prompt formaté
    """
    return """Tu es un traducteur spécialisé dans les hadiths du Prophète Muhammad ﷺ.
Tu traduis UNIQUEMENT du texte arabe vers le français.

RÈGLES ABSOLUES — LEXIQUE DE FER :
1. استوى → "S'est établi" (jamais d'autre formulation)
2. يد الله / يده → "la Main d'Allah" / "Sa Main" (littéral uniquement)
3. وجه الله / وجهه → "la Face d'Allah" / "Sa Face" (littéral uniquement)
4. نزل / ينزل → "descend" / "descendra" (jamais "se manifeste")
5. فوق / العلو → "au-dessus" / "l'élévation" (jamais "au-delà" ou métaphore)
6. الرحمة → "la Miséricorde" (si attribut d'Allah), "la miséricorde" (si autre)
7. الغضب → "la Colère" (si attribut d'Allah, littéral, sans ta'wîl)
8. المحبة / الحب → "l'Amour" (si attribut d'Allah, littéral)

INTERDICTIONS :
- Aucune explication ou commentaire dans la traduction
- Aucun ajout entre parenthèses pour "expliquer" les attributs
- Aucun ta'wîl (réinterprétation) des attributs d'Allah
- Aucune traduction par "puissance", "essence", "grâce" à la place d'attributs littéraux

STYLE :
- Traduction claire, lisible en français moderne
- Conserver le style solennel des hadiths
- Noms propres arabes en translittération standard islamique

Traduis maintenant ce hadith en français en respectant ces règles :
"""

def appliquer_lexique_post_traduction(texte_traduit: str) -> str:
    """
    Corriger une traduction existante pour la rendre conforme au Lexique de Fer
    
    Args:
        texte_traduit: Traduction française à corriger
        
    Returns:
        Traduction corrigée
    """
    corrections = {
        # Corrections courantes de ta'wîl
        r'\bpuissance d\'Allah\b': 'la Main d\'Allah',
        r'\bsa puissance\b': 'Sa Main',
        r'\bessence d\'Allah\b': 'la Face d\'Allah',
        r'\bson essence\b': 'Sa Face',
        r'\bse manifeste\b': 'descend',
        r'\bau-delà\b': 'au-dessus',
        r'\bs\'élève\b': 'S\'est établi',
        r'\bs\'installe\b': 'S\'est établi',
    }
    
    texte_corrige = texte_traduit
    for pattern, remplacement in corrections.items():
        texte_corrige = re.sub(pattern, remplacement, texte_corrige, flags=re.IGNORECASE)
    
    return texte_corrige

# ============================================================
# VALIDATION ET TESTS
# ============================================================

def test_lexique():
    """Tests unitaires du Lexique de Fer"""
    print("=== TESTS LEXIQUE DE FER ===\n")
    
    # Test 1: Traduction conforme
    test1 = "la Main d'Allah est au-dessus de leurs mains"
    conforme1, erreurs1 = verifier_conformite(test1)
    print(f"Test 1 (conforme): {'✅' if conforme1 else '❌'}")
    
    # Test 2: Traduction non conforme (ta'wîl)
    test2 = "la puissance d'Allah est au-dessus de leurs mains"
    conforme2, erreurs2 = verifier_conformite(test2)
    print(f"Test 2 (non conforme): {'✅' if not conforme2 else '❌'}")
    if erreurs2:
        for err in erreurs2:
            print(f"  {err}")
    
    # Test 3: Correction post-traduction
    test3 = "Allah se manifeste dans le ciel avec Sa puissance"
    test3_corrige = appliquer_lexique_post_traduction(test3)
    print(f"\nTest 3 (correction):")
    print(f"  Avant: {test3}")
    print(f"  Après: {test3_corrige}")
    
    # Test 4: Prompt complet
    print(f"\nTest 4 (prompt):")
    prompt = get_prompt_lexique_fer()
    print(f"  Longueur prompt: {len(prompt)} caractères")
    print(f"  Contient 'LEXIQUE DE FER': {'✅' if 'LEXIQUE DE FER' in prompt else '❌'}")

# ============================================================
# INTÉGRATION AVEC CLAUDE/LLM
# ============================================================

def preparer_requete_traduction(texte_arabe: str) -> Dict:
    """
    Préparer une requête de traduction pour Claude avec Lexique de Fer
    
    Args:
        texte_arabe: Texte arabe à traduire
        
    Returns:
        Dict avec prompt et paramètres
    """
    return {
        'system': get_prompt_lexique_fer(),
        'messages': [
            {
                'role': 'user',
                'content': texte_arabe
            }
        ],
        'model': 'claude-3-haiku-20240307',
        'max_tokens': 1000,
        'temperature': 0.3  # Basse température pour traduction précise
    }

def valider_reponse_claude(reponse_claude: str) -> Tuple[bool, str, List[str]]:
    """
    Valider la réponse de Claude et appliquer corrections si nécessaire
    
    Args:
        reponse_claude: Traduction retournée par Claude
        
    Returns:
        (valide, texte_final, erreurs)
    """
    # Vérifier conformité
    conforme, erreurs = verifier_conformite(reponse_claude)
    
    if conforme:
        return True, reponse_claude, []
    
    # Tenter correction automatique
    texte_corrige = appliquer_lexique_post_traduction(reponse_claude)
    
    # Re-vérifier après correction
    conforme_apres, erreurs_apres = verifier_conformite(texte_corrige)
    
    if conforme_apres:
        return True, texte_corrige, ['Correction automatique appliquée']
    else:
        return False, texte_corrige, erreurs_apres

if __name__ == '__main__':
    test_lexique()