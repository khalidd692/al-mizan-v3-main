"""
API Endpoints pour les Outils de Médine
Intégration des connecteurs dans l'API Al-Mīzān
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
import logging

# Import des connecteurs
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from connectors.islamdb_connector import IslamDBConnector
from connectors.dorar_connector_enhanced import DorarConnectorEnhanced
from connectors.islamweb_connector import IslamWebConnector
from connectors.shamela_connector import ShamelaConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter(prefix="/api/v1/medine", tags=["Medine Tools"])

# ============================================================================
# ENDPOINT 1: Analyse des Narrateurs (Jarh wa Ta'dil)
# ============================================================================

@router.get("/narrator/{narrator_name}")
async def get_narrator_analysis(
    narrator_name: str,
    include_salafi_opinions: bool = Query(True, description="Inclure les avis des savants salafis")
):
    """
    Analyse complète d'un narrateur selon la méthodologie de Médine
    
    Retourne tous les avis des imams du Jarh wa Ta'dil sans filtrage.
    
    Args:
        narrator_name: Nom du narrateur en arabe
        include_salafi_opinions: Inclure les avis d'Al-Albani, Ibn Baz, etc.
    
    Returns:
        {
            'narrator': {...},
            'jarh_tadil_opinions': [...],
            'salafi_opinions': [...],
            'technical_terms': [...],
            'reliability_score': 0.95
        }
    """
    try:
        async with IslamDBConnector() as connector:
            result = await connector.get_narrator_info(
                narrator_name,
                include_salafi_opinions=include_salafi_opinions
            )
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Narrateur '{narrator_name}' non trouvé"
                )
            
            return {
                "success": True,
                "data": result,
                "source": "islamdb.com",
                "methodology": "Jarh wa Ta'dil - Données brutes non filtrées"
            }
    
    except Exception as e:
        logger.error(f"Erreur analyse narrateur: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 2: Vérification du Matn (Texte du Hadith)
# ============================================================================

@router.post("/verify-matn")
async def verify_hadith_text(
    hadith_text: str = Query(..., description="Texte du hadith à vérifier"),
    detect_variants: bool = Query(True, description="Détecter les variantes textuelles")
):
    """
    Vérifie et normalise le texte d'un hadith avec détection des variantes
    
    Identifie l'édition de référence et les différences entre éditions.
    
    Args:
        hadith_text: Texte du hadith en arabe
        detect_variants: Activer la détection des variantes
    
    Returns:
        {
            'normalized_text': '...',
            'variants': [...],
            'reference_edition': {...},
            'confidence': 0.95
        }
    """
    try:
        async with DorarConnectorEnhanced() as connector:
            result = await connector.verify_matn(hadith_text)
            
            if result.get('error'):
                raise HTTPException(
                    status_code=404,
                    detail="Hadith non trouvé dans les sources"
                )
            
            # Filtrer les variantes si non demandées
            if not detect_variants:
                result['variants'] = []
            
            return {
                "success": True,
                "data": result,
                "source": "dorar.net",
                "methodology": "Tahqīq - Édition critique"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur vérification Matn: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 3: Récupération d'un Hadith par Numéro
# ============================================================================

@router.get("/hadith/{book}/{hadith_number}")
async def get_hadith_by_number(
    book: str,
    hadith_number: int,
    include_edition: bool = Query(True, description="Inclure les détails de l'édition")
):
    """
    Récupère un hadith spécifique avec ses détails d'édition
    
    Args:
        book: Nom du livre (bukhari, muslim, abu_dawud, etc.)
        hadith_number: Numéro du hadith
        include_edition: Inclure éditeur, maison d'édition, année
    
    Returns:
        {
            'text': '...',
            'source': '...',
            'edition': {...}
        }
    """
    try:
        async with DorarConnectorEnhanced() as connector:
            result = await connector.get_hadith_by_number(book, hadith_number)
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Hadith {book} #{hadith_number} non trouvé"
                )
            
            # Filtrer l'édition si non demandée
            if not include_edition:
                result.pop('edition', None)
            
            return {
                "success": True,
                "data": result,
                "source": "dorar.net"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération hadith: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 4: Commentaire (Sharh) d'un Hadith
# ============================================================================

@router.get("/sharh/{book}/{hadith_number}")
async def get_hadith_commentary(
    book: str,
    hadith_number: int,
    sharh_book: str = Query("fath_al_bari", description="Livre de commentaire"),
    include_key_points: bool = Query(True, description="Inclure les points clés")
):
    """
    Récupère le commentaire d'un hadith depuis les livres classiques
    
    Args:
        book: Livre source (bukhari, muslim, etc.)
        hadith_number: Numéro du hadith
        sharh_book: Livre de commentaire (fath_al_bari, sharh_muslim, etc.)
        include_key_points: Inclure l'extraction des Fawa'id
    
    Returns:
        {
            'book': 'فتح الباري',
            'author': 'ابن حجر العسقلاني',
            'edition': {...},
            'volume': 1,
            'page': 45,
            'commentary': '...',
            'key_points': [...]
        }
    """
    try:
        async with IslamWebConnector() as connector:
            result = await connector.get_sharh(book, hadith_number, sharh_book)
            
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Commentaire non trouvé pour {book} #{hadith_number}"
                )
            
            # Filtrer les points clés si non demandés
            if not include_key_points:
                result.pop('key_points', None)
            
            return {
                "success": True,
                "data": result,
                "source": "islamweb.net",
                "methodology": "Sharh classique avec références précises"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération Sharh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 5: Recherche dans les Livres de Sharh
# ============================================================================

@router.get("/sharh/search")
async def search_in_sharh(
    keyword: str = Query(..., description="Mot-clé à rechercher"),
    sharh_book: str = Query("fath_al_bari", description="Livre de commentaire"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats")
):
    """
    Recherche un mot-clé dans un livre de commentaire
    
    Args:
        keyword: Mot-clé en arabe
        sharh_book: Livre de commentaire
        limit: Nombre maximum de résultats
    
    Returns:
        Liste de résultats avec contexte
    """
    try:
        async with IslamWebConnector() as connector:
            results = await connector.search_in_sharh(keyword, sharh_book, limit)
            
            return {
                "success": True,
                "data": results,
                "total": len(results),
                "source": "islamweb.net"
            }
    
    except Exception as e:
        logger.error(f"Erreur recherche Sharh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 6: Livres de Sharh Disponibles
# ============================================================================

@router.get("/sharh/available-books")
async def get_available_sharh_books():
    """
    Liste tous les livres de Sharh disponibles avec leurs métadonnées
    
    Returns:
        Liste des livres avec auteur, édition, volumes
    """
    try:
        async with IslamWebConnector() as connector:
            books = await connector.get_available_sharh_books()
            
            return {
                "success": True,
                "data": books,
                "total": len(books)
            }
    
    except Exception as e:
        logger.error(f"Erreur liste livres Sharh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 7: Extraction Aqidah depuis Shamela
# ============================================================================

@router.post("/aqidah/extract")
async def extract_aqidah_points(
    hadith_text: str = Query(..., description="Texte du hadith"),
    include_salaf_positions: bool = Query(True, description="Inclure positions des Salaf")
):
    """
    Extrait les points de Aqidah d'un hadith depuis la Maktaba Shamela
    
    Args:
        hadith_text: Texte du hadith
        include_salaf_positions: Inclure les positions des Salaf
    
    Returns:
        {
            'aqidah_points': [...],
            'salaf_positions': [...],
            'primary_sources': [...]
        }
    """
    try:
        async with ShamelaConnector() as connector:
            result = await connector.extract_aqidah_points(hadith_text)
            
            if not include_salaf_positions:
                result.pop('salaf_positions', None)
            
            return {
                "success": True,
                "data": result,
                "source": "shamela.ws",
                "methodology": "Extraction depuis livres de Aqidah salafie"
            }
    
    except Exception as e:
        logger.error(f"Erreur extraction Aqidah: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 8: Analyse Complète (Combo)
# ============================================================================

@router.post("/analyze-complete")
async def complete_hadith_analysis(
    hadith_text: str = Query(..., description="Texte du hadith"),
    book: Optional[str] = Query(None, description="Livre source si connu"),
    hadith_number: Optional[int] = Query(None, description="Numéro si connu")
):
    """
    Analyse complète d'un hadith selon la méthodologie de Médine
    
    Combine tous les outils:
    - Vérification du Matn
    - Analyse des narrateurs
    - Commentaire classique
    - Extraction Aqidah
    
    Args:
        hadith_text: Texte du hadith
        book: Livre source (optionnel)
        hadith_number: Numéro (optionnel)
    
    Returns:
        Analyse complète avec toutes les données
    """
    try:
        result = {
            "hadith_text": hadith_text,
            "matn_verification": None,
            "sharh": None,
            "aqidah": None
        }
        
        # 1. Vérifier le Matn
        async with DorarConnectorEnhanced() as connector:
            result["matn_verification"] = await connector.verify_matn(hadith_text)
        
        # 2. Récupérer le Sharh si livre et numéro fournis
        if book and hadith_number:
            async with IslamWebConnector() as connector:
                result["sharh"] = await connector.get_sharh(book, hadith_number)
        
        # 3. Extraire les points de Aqidah
        async with ShamelaConnector() as connector:
            result["aqidah"] = await connector.extract_aqidah_points(hadith_text)
        
        return {
            "success": True,
            "data": result,
            "methodology": "Analyse complète - Outils de Médine"
        }
    
    except Exception as e:
        logger.error(f"Erreur analyse complète: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINT 9: Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Vérifie que tous les connecteurs sont opérationnels
    """
    status = {
        "islamdb": False,
        "dorar": False,
        "islamweb": False,
        "shamela": False
    }
    
    try:
        # Test IslamDB
        async with IslamDBConnector() as conn:
            status["islamdb"] = True
    except:
        pass
    
    try:
        # Test Dorar
        async with DorarConnectorEnhanced() as conn:
            status["dorar"] = True
    except:
        pass
    
    try:
        # Test IslamWeb
        async with IslamWebConnector() as conn:
            status["islamweb"] = True
    except:
        pass
    
    try:
        # Test Shamela
        async with ShamelaConnector() as conn:
            status["shamela"] = True
    except:
        pass
    
    all_healthy = all(status.values())
    
    return {
        "success": all_healthy,
        "connectors": status,
        "message": "Tous les connecteurs opérationnels" if all_healthy else "Certains connecteurs indisponibles"
    }