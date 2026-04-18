"""Al-Mīzān v5.0 — Agent Validateur Unifié (Haiku + Sonnet si nécessaire)."""

import json
from typing import Dict, Any, Optional
from anthropic import Anthropic

from backend.utils.logging import get_logger
from backend.utils.constitution import run_full_doctrinal_check

log = get_logger("mizan.agent.validator")

class AgentValidator:
    """Agent validateur unifié pour normalisation, traduction et validation savant."""
    
    # Grades normalisés autorisés
    VALID_GRADES = ["صحيح", "حسن", "ضعيف", "موضوع"]
    
    # Hiérarchie des localisations de savants (priorité décroissante)
    SCHOLAR_LOCATIONS = {
        "Médine": 1,
        "Arabie Saoudite": 2,
        "TAWAQQUF": 3  # Inconnu ou déviant
    }
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.mock_mode = not api_key or api_key == ""
    
    async def validate_hadith(self, hadith_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Valide un hadith brut et retourne le résultat structuré.
        
        Args:
            hadith_raw: Dict avec dorar_id, matn_ar, source, grade_raw, rawi
        
        Returns:
            Dict avec:
            - grade_normalized: Grade normalisé (صحيح/حسن/ضعيف/موضوع)
            - translation_fr: Traduction française (Lexique de Fer)
            - scholar_verdict: Nom du savant validé
            - scholar_location: Médine / Arabie Saoudite / TAWAQQUF
            - confidence_score: 0-100
            - reasoning: Explication du verdict
        """
        if self.mock_mode:
            return self._mock_validation(hadith_raw)
        
        # Étape 1: Normalisation du grade avec Haiku
        grade_result = await self._normalize_grade_haiku(hadith_raw)
        
        # Étape 2: Traduction avec Haiku
        translation_result = await self._translate_haiku(hadith_raw)

        # Étape 2b: Contrôle doctrinal de la traduction (regex, coût LLM = 0)
        # Doit précéder toute escalade Sonnet — un ta'wîl détecté ici est bloquant.
        _tawaqquf_doc, _doc_report = run_full_doctrinal_check(
            text_ar=hadith_raw.get('matn_ar', ''),
            text_fr=translation_result.get('translation', ''),
        )
        if _tawaqquf_doc:
            log.warning(f"[VALIDATOR] Tawaqquf doctrinal forcé — {_doc_report[:120]}")
            return {
                "grade_normalized": "TAWAQQUF",
                "translation_fr": translation_result.get('translation', ''),
                "scholar_verdict": "TAWAQQUF",
                "scholar_location": "TAWAQQUF",
                "confidence_score": 0.0,
                "reasoning": _doc_report,
                "tawaqquf": True,
                "tawaqquf_reasons": ["terme_protege_detecte"],
            }

        # Étape 3: Validation savant avec Haiku
        scholar_result = await self._validate_scholar_haiku(hadith_raw, grade_result)
        
        # Calculer confiance globale
        confidence = self._calculate_confidence(grade_result, scholar_result)
        
        # Étape 4: Si confiance < 80, vérification avec Sonnet
        if confidence < 80:
            log.info(f"[VALIDATOR] Confiance {confidence:.1f}% < 80, escalade vers Sonnet")
            sonnet_result = await self._verify_with_sonnet(
                hadith_raw, grade_result, scholar_result, translation_result
            )
            confidence = sonnet_result["confidence_score"]
            scholar_result = sonnet_result["scholar"]
            grade_result = sonnet_result["grade"]
        
        return {
            "grade_normalized": grade_result["grade"],
            "translation_fr": translation_result["translation"],
            "scholar_verdict": scholar_result["scholar_name"],
            "scholar_location": scholar_result["location"],
            "confidence_score": confidence,
            "reasoning": scholar_result["reasoning"],
            "tawaqquf": False,
            "tawaqquf_reasons": [],
        }
    
    async def _normalize_grade_haiku(self, hadith: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise le grade avec Claude Haiku."""
        prompt = f"""Tu es un expert en sciences du Hadith. Normalise le grade suivant.

Hadith:
- Source: {hadith.get('source', 'Inconnue')}
- Grade brut: {hadith.get('grade_raw', 'Non spécifié')}

Règles STRICTES:
1. Grades autorisés UNIQUEMENT: صحيح (sahih), حسن (hasan), ضعيف (daif), موضوع (mawdu)
2. Si grade inconnu ou ambigu: ضعيف par défaut
3. JAMAIS inventer un grade

Réponds en JSON:
{{
  "grade": "صحيح",
  "confidence": 95,
  "reasoning": "Explication courte"
}}"""

        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        log.debug(f"[VALIDATOR] Grade normalisé: {result['grade']} (confiance: {result['confidence']}%)")
        return result
    
    async def _translate_haiku(self, hadith: Dict[str, Any]) -> Dict[str, Any]:
        """Traduit le matn en français avec Lexique de Fer."""
        prompt = f"""Traduis ce hadith en français avec le Lexique de Fer (termes techniques non traduits).

Matn arabe:
{hadith['matn_ar']}

Règles:
1. Termes techniques en arabe (ex: Ṣaḥābah, Isnād, Jarḥ wa Taʿdīl)
2. Traduction littérale, pas d'interprétation
3. Maximum 2 phrases

Réponds en JSON:
{{
  "translation": "Traduction française ici"
}}"""

        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        return result
    
    async def _validate_scholar_haiku(
        self,
        hadith: Dict[str, Any],
        grade_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valide le savant selon hiérarchie Médine > Arabie Saoudite > TAWAQQUF."""
        prompt = f"""Tu es un expert en Jarḥ wa Taʿdīl. Identifie le savant qui a authentifié ce hadith.

Hadith:
- Source: {hadith.get('source', 'Inconnue')}
- Grade: {grade_result['grade']}

Hiérarchie STRICTE (priorité décroissante):
1. Médine (ex: al-Bukhārī, Muslim, Mālik, Aḥmad)
2. Arabie Saoudite (ex: Ibn Bāz, al-Albānī, Ibn ʿUthaymīn)
3. TAWAQQUF (si savant inconnu, déviant, ou non Salaf as-Salih)

Règles ABSOLUES:
- JAMAIS utiliser le terme "Salafi" → "Salaf as-Salih" uniquement
- Si savant inconnu ou douteux: TAWAQQUF
- Pas d'innovation, pas de Bidʿah

Réponds en JSON:
{{
  "scholar_name": "Nom du savant",
  "location": "Médine",
  "confidence": 90,
  "reasoning": "Explication courte"
}}"""

        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        
        # Vérifier que la location est valide
        if result["location"] not in self.SCHOLAR_LOCATIONS:
            log.warning(f"[VALIDATOR] Location invalide: {result['location']}, défaut TAWAQQUF")
            result["location"] = "TAWAQQUF"
            result["confidence"] = min(result["confidence"], 50)
        
        return result
    
    async def _verify_with_sonnet(
        self,
        hadith: Dict[str, Any],
        grade_result: Dict[str, Any],
        scholar_result: Dict[str, Any],
        translation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Vérification finale avec Claude Sonnet si confiance < 80."""
        prompt = f"""Tu es un muḥaddith expert. Vérifie ce verdict de hadith.

Hadith:
- Matn: {hadith['matn_ar']}
- Source: {hadith.get('source')}
- Grade proposé: {grade_result['grade']}
- Savant proposé: {scholar_result['scholar_name']} ({scholar_result['location']})
- Traduction: {translation_result['translation']}

Vérifie:
1. Grade correct selon les Mutaqaddimūn ?
2. Savant valide selon hiérarchie Médine > Arabie Saoudite > TAWAQQUF ?
3. Pas de Bidʿah, pas de déviation ?

Réponds en JSON:
{{
  "grade": {{"grade": "صحيح", "confidence": 95}},
  "scholar": {{"scholar_name": "al-Bukhārī", "location": "Médine", "confidence": 95, "reasoning": "..."}},
  "confidence_score": 95,
  "corrections": "Corrections si nécessaire"
}}"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = json.loads(response.content[0].text)
        log.info(f"[VALIDATOR] Sonnet vérification: confiance={result['confidence_score']}%")
        return result
    
    def _calculate_confidence(
        self,
        grade_result: Dict[str, Any],
        scholar_result: Dict[str, Any]
    ) -> float:
        """Calcule la confiance globale."""
        grade_conf = grade_result.get("confidence", 50)
        scholar_conf = scholar_result.get("confidence", 50)
        
        # Pénalité si TAWAQQUF
        if scholar_result.get("location") == "TAWAQQUF":
            scholar_conf *= 0.7
        
        # Moyenne pondérée (grade 60%, savant 40%)
        confidence = (grade_conf * 0.6) + (scholar_conf * 0.4)
        return round(confidence, 1)
    
    def _mock_validation(self, hadith: Dict[str, Any]) -> Dict[str, Any]:
        """Validation mockée pour tests."""
        log.debug("[VALIDATOR] Mode MOCK actif")
        
        return {
            "grade_normalized": "صحيح",
            "translation_fr": f"Traduction mockée de: {hadith['matn_ar'][:50]}...",
            "scholar_verdict": "al-Bukhārī",
            "scholar_location": "Médine",
            "confidence_score": 92.0,
            "reasoning": "Validation mockée pour tests"
        }