"""Al-Mīzān v5.0 — Harvester Dorar.net avec checkpoint."""

import asyncio
import json
import pathlib
from typing import Optional, Dict, Any
from datetime import datetime

from backend.dorar.client import DorarClient
from backend.corpus.db import CorpusDB
from backend.utils.logging import get_logger

log = get_logger("mizan.harvester")

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKPOINT_FILE = _REPO_ROOT / "corpus" / "harvester_checkpoint.json"

class HadithHarvester:
    """Harvester avec checkpoint de reprise pour aspirer hadiths depuis Dorar.net."""
    
    def __init__(
        self,
        start_id: int = 1,
        target_count: int = 1000,
        rate_limit: float = 2.0
    ):
        self.start_id = start_id
        self.target_count = target_count
        self.rate_limit = rate_limit
        self.db = CorpusDB()
        
        # Statistiques
        self.stats = {
            "total_attempted": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_duplicates": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _load_checkpoint(self) -> Dict[str, Any]:
        """Charge le checkpoint de reprise."""
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                log.info(f"[HARVESTER] Checkpoint chargé: {checkpoint}")
                return checkpoint
            except Exception as e:
                log.warning(f"[HARVESTER] Erreur lecture checkpoint: {e}")
        
        return {
            "last_id": self.start_id - 1,
            "total_harvested": 0,
            "last_update": None
        }
    
    def _save_checkpoint(self, last_id: int, total_harvested: int):
        """Sauvegarde le checkpoint."""
        checkpoint = {
            "last_id": last_id,
            "total_harvested": total_harvested,
            "last_update": datetime.now().isoformat()
        }
        
        try:
            CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            log.debug(f"[HARVESTER] Checkpoint sauvegardé: last_id={last_id}")
        except Exception as e:
            log.error(f"[HARVESTER] Erreur sauvegarde checkpoint: {e}")
    
    async def harvest(self, resume: bool = True) -> Dict[str, Any]:
        """Lance le harvesting avec reprise optionnelle.
        
        Args:
            resume: Si True, reprend depuis le dernier checkpoint
        
        Returns:
            Statistiques du harvesting
        """
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Charger checkpoint si reprise
        checkpoint = self._load_checkpoint() if resume else None
        
        if checkpoint and resume:
            current_id = checkpoint["last_id"] + 1
            already_harvested = checkpoint["total_harvested"]
            remaining = self.target_count - already_harvested
            
            log.info(
                f"[HARVESTER] Reprise depuis checkpoint: "
                f"ID={current_id}, déjà récupérés={already_harvested}, "
                f"restants={remaining}"
            )
        else:
            current_id = self.start_id
            already_harvested = 0
            remaining = self.target_count
            log.info(f"[HARVESTER] Démarrage nouveau: ID={current_id}, cible={self.target_count}")
        
        # Harvesting
        async with DorarClient(rate_limit=self.rate_limit) as client:
            for i in range(remaining):
                hadith_id = str(current_id + i)
                self.stats["total_attempted"] += 1
                
                log.info(
                    f"[HARVESTER] Progression: {i+1}/{remaining} "
                    f"(ID={hadith_id}, total={already_harvested + i + 1}/{self.target_count})"
                )
                
                # Récupérer hadith
                hadith = await client.fetch_hadith_by_id(hadith_id)
                
                if hadith:
                    # Insérer en base
                    result = await self.db.insert_raw_hadith(
                        dorar_id=hadith["dorar_id"],
                        matn_ar=hadith["matn_ar"],
                        source=hadith.get("source"),
                        grade_raw=hadith.get("grade_raw"),
                        rawi=hadith.get("rawi")
                    )
                    
                    if result > 0:
                        self.stats["total_success"] += 1
                    else:
                        self.stats["total_duplicates"] += 1
                else:
                    self.stats["total_failed"] += 1
                
                # Sauvegarder checkpoint tous les 10 hadiths
                if (i + 1) % 10 == 0:
                    self._save_checkpoint(
                        last_id=int(hadith_id),
                        total_harvested=already_harvested + i + 1
                    )
        
        # Checkpoint final
        self._save_checkpoint(
            last_id=current_id + remaining - 1,
            total_harvested=already_harvested + remaining
        )
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        log.info(
            f"[HARVESTER] Terminé: "
            f"succès={self.stats['total_success']}, "
            f"échecs={self.stats['total_failed']}, "
            f"doublons={self.stats['total_duplicates']}"
        )
        
        return self.stats
    
    async def harvest_with_callback(self, progress_callback=None):
        """Harvest avec callback de progression pour SSE.
        
        Args:
            progress_callback: Fonction async appelée après chaque hadith
                              avec (hadith_id, current, total, stats)
        """
        self.stats["start_time"] = datetime.now().isoformat()
        
        checkpoint = self._load_checkpoint()
        current_id = checkpoint["last_id"] + 1 if checkpoint else self.start_id
        already_harvested = checkpoint["total_harvested"] if checkpoint else 0
        remaining = self.target_count - already_harvested
        
        async with DorarClient(rate_limit=self.rate_limit) as client:
            for i in range(remaining):
                hadith_id = str(current_id + i)
                self.stats["total_attempted"] += 1
                
                hadith = await client.fetch_hadith_by_id(hadith_id)
                
                if hadith:
                    result = await self.db.insert_raw_hadith(
                        dorar_id=hadith["dorar_id"],
                        matn_ar=hadith["matn_ar"],
                        source=hadith.get("source"),
                        grade_raw=hadith.get("grade_raw"),
                        rawi=hadith.get("rawi")
                    )
                    
                    if result > 0:
                        self.stats["total_success"] += 1
                    else:
                        self.stats["total_duplicates"] += 1
                else:
                    self.stats["total_failed"] += 1
                
                # Callback progression
                if progress_callback:
                    await progress_callback(
                        hadith_id=hadith_id,
                        current=already_harvested + i + 1,
                        total=self.target_count,
                        stats=self.stats.copy()
                    )
                
                # Checkpoint périodique
                if (i + 1) % 10 == 0:
                    self._save_checkpoint(
                        last_id=int(hadith_id),
                        total_harvested=already_harvested + i + 1
                    )
        
        self._save_checkpoint(
            last_id=current_id + remaining - 1,
            total_harvested=already_harvested + remaining
        )
        
        self.stats["end_time"] = datetime.now().isoformat()
        return self.stats

async def main():
    """Point d'entrée CLI pour le harvester."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Al-Mīzān Hadith Harvester")
    parser.add_argument("--start-id", type=int, default=1, help="ID de départ")
    parser.add_argument("--count", type=int, default=1000, help="Nombre de hadiths")
    parser.add_argument("--rate-limit", type=float, default=2.0, help="Secondes entre requêtes")
    parser.add_argument("--no-resume", action="store_true", help="Ne pas reprendre depuis checkpoint")
    
    args = parser.parse_args()
    
    harvester = HadithHarvester(
        start_id=args.start_id,
        target_count=args.count,
        rate_limit=args.rate_limit
    )
    
    stats = await harvester.harvest(resume=not args.no_resume)
    
    print("\n" + "="*60)
    print("STATISTIQUES HARVESTING")
    print("="*60)
    print(f"Tentatives:  {stats['total_attempted']}")
    print(f"Succès:      {stats['total_success']}")
    print(f"Échecs:      {stats['total_failed']}")
    print(f"Doublons:    {stats['total_duplicates']}")
    print(f"Début:       {stats['start_time']}")
    print(f"Fin:         {stats['end_time']}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())