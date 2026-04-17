"""Al-Mīzān v5.0 — Client Dorar.net avec rate limiting."""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import json
from datetime import datetime

from backend.utils.logging import get_logger

log = get_logger("mizan.dorar.client")

class DorarClient:
    """Client async pour aspirer hadiths depuis Dorar.net."""
    
    BASE_URL = "https://dorar.net"
    RATE_LIMIT_SECONDS = 2.0  # 2 secondes entre chaque requête
    
    def __init__(self, rate_limit: float = RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Al-Mizan Research Bot/5.0 (Academic Purpose)",
                "Accept": "text/html,application/json",
                "Accept-Language": "ar,en"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit_wait(self):
        """Applique le rate limiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_request_time
        
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            log.debug(f"[DORAR] Rate limiting: attente {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def fetch_hadith_by_id(self, hadith_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un hadith par son ID Dorar.net.
        
        Args:
            hadith_id: ID du hadith sur Dorar.net (ex: "1234")
        
        Returns:
            Dict avec matn_ar, source, grade_raw, rawi, ou None si erreur
        """
        if not self.session:
            raise RuntimeError("Client non initialisé. Utiliser 'async with DorarClient()'")
        
        await self._rate_limit_wait()
        
        url = f"{self.BASE_URL}/hadith/{hadith_id}"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    log.warning(f"[DORAR] Erreur HTTP {response.status} pour ID {hadith_id}")
                    return None
                
                html = await response.text()
                return self._parse_hadith_page(html, hadith_id)
        
        except asyncio.TimeoutError:
            log.error(f"[DORAR] Timeout pour ID {hadith_id}")
            return None
        except Exception as e:
            log.exception(f"[DORAR] Erreur lors de la récupération ID {hadith_id}: {e}")
            return None
    
    def _parse_hadith_page(self, html: str, hadith_id: str) -> Optional[Dict[str, Any]]:
        """Parse une page HTML de hadith Dorar.net.
        
        Note: Cette implémentation est un template. La structure exacte
        dépend du HTML réel de Dorar.net et devra être ajustée.
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # IMPORTANT: Ces sélecteurs CSS sont des PLACEHOLDERS
            # Ils doivent être ajustés selon la structure réelle de Dorar.net
            
            # Texte arabe du hadith
            matn_elem = soup.select_one('.hadith-text, .matn, [class*="hadith"]')
            matn_ar = matn_elem.get_text(strip=True) if matn_elem else None
            
            # Source (ex: Ṣaḥīḥ al-Bukhārī n°1)
            source_elem = soup.select_one('.hadith-source, .source, [class*="source"]')
            source = source_elem.get_text(strip=True) if source_elem else None
            
            # Grade (ex: صحيح)
            grade_elem = soup.select_one('.hadith-grade, .grade, [class*="grade"]')
            grade_raw = grade_elem.get_text(strip=True) if grade_elem else None
            
            # Narrateur principal
            rawi_elem = soup.select_one('.hadith-rawi, .rawi, [class*="rawi"]')
            rawi = rawi_elem.get_text(strip=True) if rawi_elem else None
            
            if not matn_ar:
                log.warning(f"[DORAR] Matn non trouvé pour ID {hadith_id}")
                return None
            
            result = {
                "dorar_id": hadith_id,
                "matn_ar": matn_ar,
                "source": source,
                "grade_raw": grade_raw,
                "rawi": rawi
            }
            
            log.debug(f"[DORAR] Hadith parsé: ID={hadith_id}, source={source}")
            return result
        
        except Exception as e:
            log.exception(f"[DORAR] Erreur parsing HTML pour ID {hadith_id}: {e}")
            return None
    
    async def fetch_hadith_range(
        self,
        start_id: int,
        count: int,
        checkpoint_callback=None
    ) -> List[Dict[str, Any]]:
        """Récupère une plage de hadiths.
        
        Args:
            start_id: ID de départ
            count: Nombre de hadiths à récupérer
            checkpoint_callback: Fonction appelée après chaque hadith (pour sauvegarde)
        
        Returns:
            Liste des hadiths récupérés avec succès
        """
        hadiths = []
        
        for i in range(count):
            hadith_id = str(start_id + i)
            
            log.info(f"[DORAR] Récupération {i+1}/{count}: ID={hadith_id}")
            
            hadith = await self.fetch_hadith_by_id(hadith_id)
            
            if hadith:
                hadiths.append(hadith)
                
                if checkpoint_callback:
                    await checkpoint_callback(hadith, i + 1, count)
            else:
                log.warning(f"[DORAR] Échec récupération ID {hadith_id}")
        
        log.info(f"[DORAR] Récupération terminée: {len(hadiths)}/{count} hadiths")
        return hadiths
    
    async def search_hadiths(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Recherche de hadiths par mot-clé.
        
        Note: Nécessite l'API de recherche Dorar.net ou scraping de la page de résultats.
        Cette implémentation est un placeholder.
        """
        if not self.session:
            raise RuntimeError("Client non initialisé")
        
        await self._rate_limit_wait()
        
        # Placeholder: à implémenter selon l'API/structure réelle de Dorar.net
        log.warning("[DORAR] search_hadiths() non implémenté - nécessite API Dorar.net")
        return []