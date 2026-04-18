"""
Lexique de Fer - Protection des termes de Aqida
Système de routage HARD/SOFT pour garantir la sécurité théologique
"""

# Termes HARD : Nécessitent obligatoirement Claude Sonnet 3.5
HARD_TERMS = {
    # Attributs divins sensibles
    "yad": ["يد", "يدين", "يداه", "main", "mains"],
    "istawa": ["استوى", "استواء", "s'est établi", "établissement"],
    "nuzul": ["نزول", "ينزل", "descente", "descend"],
    "wajh": ["وجه", "وجهه", "face", "visage"],
    "ayn": ["عين", "عينين", "œil", "yeux"],
    "qadam": ["قدم", "pied"],
    "saq": ["ساق", "jambe"],
    "isba": ["إصبع", "أصابع", "doigt", "doigts"],
    
    # Concepts théologiques critiques
    "tajsim": ["تجسيم", "anthropomorphisme", "corporalisme"],
    "tashbih": ["تشبيه", "assimilation", "ressemblance"],
    "ta'til": ["تعطيل", "négation", "privation"],
    "tahrif": ["تحريف", "altération", "déformation"],
    "tafwid": ["تفويض", "délégation"],
    "ta'wil": ["تأويل", "interprétation"],
    
    # Noms et attributs
    "sifat": ["صفات", "attributs"],
    "asma": ["أسماء", "noms"],
    "dhat": ["ذات", "essence"],
    
    # Questions de croyance
    "ru'ya": ["رؤية", "vision"],
    "kalam": ["كلام", "parole"],
    "khalq": ["خلق القرآن", "création du coran"],
}

# Termes SOFT : Peuvent utiliser Haiku mais avec vigilance
SOFT_TERMS = {
    "iman": ["إيمان", "foi"],
    "kufr": ["كفر", "mécréance"],
    "shirk": ["شرك", "association"],
    "tawhid": ["توحيد", "unicité"],
    "qadar": ["قدر", "destin"],
    "qadr": ["قدر", "prédestination"],
}

def detect_term_level(text: str) -> tuple[str, list[str]]:
    """
    Détecte le niveau de sensibilité théologique d'un texte
    
    Returns:
        tuple: (level, matched_terms)
        - level: "HARD", "SOFT", ou "SAFE"
        - matched_terms: liste des termes détectés
    """
    text_lower = text.lower()
    matched_hard = []
    matched_soft = []
    
    # Vérification HARD
    for category, terms in HARD_TERMS.items():
        for term in terms:
            if term.lower() in text_lower:
                matched_hard.append(f"{category}:{term}")
    
    if matched_hard:
        return "HARD", matched_hard
    
    # Vérification SOFT
    for category, terms in SOFT_TERMS.items():
        for term in terms:
            if term.lower() in text_lower:
                matched_soft.append(f"{category}:{term}")
    
    if matched_soft:
        return "SOFT", matched_soft
    
    return "SAFE", []

def get_required_model(level: str) -> str:
    """
    Retourne le modèle requis selon le niveau de sensibilité
    
    Args:
        level: "HARD", "SOFT", ou "SAFE"
    
    Returns:
        str: Nom du modèle Claude à utiliser
    """
    if level == "HARD":
        return "claude-3-5-sonnet-20241022"
    elif level == "SOFT":
        return "claude-3-5-haiku-20241022"  # Avec vigilance
    else:
        return "claude-3-5-haiku-20241022"  # Par défaut

def should_force_sonnet(text: str) -> tuple[bool, str]:
    """
    Détermine si Sonnet 3.5 doit être forcé
    
    Returns:
        tuple: (force_sonnet, reason)
    """
    level, matched = detect_term_level(text)
    
    if level == "HARD":
        return True, f"Termes HARD détectés: {', '.join(matched)}"
    
    return False, ""

def validate_response_safety(response: dict) -> tuple[bool, str]:
    """
    Valide qu'une réponse IA est sûre théologiquement
    
    Returns:
        tuple: (is_safe, error_message)
    """
    # Vérification du format JSON
    if not isinstance(response, dict):
        return False, "Format de réponse invalide"
    
    # Vérification des champs obligatoires
    required_fields = ["analysis"]
    for field in required_fields:
        if field not in response:
            return False, f"Champ manquant: {field}"
    
    # Vérification de la section Aqida
    if "aqidah" in response.get("analysis", {}):
        aqidah = response["analysis"]["aqidah"]
        
        # Si le statut n'est pas CONFORME, c'est suspect
        if aqidah.get("status") != "CONFORME":
            return False, "Statut Aqida non conforme"
        
        # Si le niveau est DANGER, bloquer
        if aqidah.get("level") == "DANGER":
            return False, "Niveau de danger théologique détecté"
    
    return True, ""

# Message de sécurité en cas de blocage
SECURITY_MESSAGE = {
    "error": True,
    "message": "Service momentanément indisponible pour raisons de sécurité.",
    "details": "Cette requête nécessite une validation supplémentaire.",
    "code": "SECURITY_BLOCK"
}