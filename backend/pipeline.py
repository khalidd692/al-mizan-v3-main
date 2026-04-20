"""Al-Mīzān v5.0 — Pipeline Harvesting + Validation + Insertion."""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

from backend.harvester import HadithHarvester
from backend.agents.agent_validator import AgentValidator
from backend.corpus.db import CorpusDB
from backend.utils.sse import emit
from backend.utils.logging import get_logger

log = get_logger("mizan.pipeline")

class ValidationPipeline:
    """Pipeline complet: Harvesting → Validation → Insertion auto."""
    
    CONFIDENCE_THRESHOLD = 85.0  # Seuil pour insertion automatique
    
    def __init__(self, api_key: str):
        self.validator = AgentValidator(api_key)
        self.db = CorpusDB()
        
        # Statistiques
        self.stats = {
            "total_harvested": 0,
            "total_validated": 0,
            "total_inserted": 0,
            "total_pending_review": 0,
            "total_failed": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def process_stream(
        self,
        start_id: int = 1,
        count: int = 1000,
        rate_limit: float = 2.0
    ) -> AsyncGenerator[str, None]:
        """Pipeline complet avec streaming SSE.
        
        Yields:
            Événements SSE de progression
        """
        self.stats["start_time"] = datetime.now().isoformat()
        
        yield emit("pipeline_start", {
            "message": "Démarrage pipeline harvesting + validation",
            "target_count": count,
            "start_id": start_id
        })
        
        # Créer harvester
        harvester = HadithHarvester(
            start_id=start_id,
            target_count=count,
            rate_limit=rate_limit
        )
        
        # Callback de progression
        async def progress_callback(hadith_id, current, total, harvest_stats):
            self.stats["total_harvested"] = harvest_stats["total_success"]
            
            yield emit("harvest_progress", {
                "hadith_id": hadith_id,
                "current": current,
                "total": total,
                "success": harvest_stats["total_success"],
                "failed": harvest_stats["total_failed"]
            })
        
        # Phase 1: Harvesting
        yield emit("phase", {"phase": 1, "name": "HARVESTING", "status": "running"})
        
        try:
            await harvester.harvest_with_callback(progress_callback)
            yield emit("phase", {"phase": 1, "name": "HARVESTING", "status": "completed"})
        except Exception as e:
            log.exception("[PIPELINE] Erreur harvesting")
            yield emit("error", {"phase": "harvesting", "message": str(e)})
            return
        
        # Phase 2: Validation et insertion
        yield emit("phase", {"phase": 2, "name": "VALIDATION", "status": "running"})
        
        # Récupérer hadiths non traités
        unprocessed = await self.db.get_unprocessed_hadiths(limit=count)
        total_to_process = len(unprocessed)

        # Règle Naqil sur les résultats FTS5
        if not unprocessed or (hasattr(unprocessed, "__getitem__") and unprocessed and unprocessed[0].get("score", 1) < 0.6):
            yield emit("naql_not_found", {
                "status": "not_found",
                "classification": "non-jugé",
                "message": "Hadith non trouvé dans la base ou score insuffisant."
            })
            return
        
        yield emit("validation_start", {
            "total_to_process": total_to_process
        })
        
        for i, hadith_raw in enumerate(unprocessed):
            try:
                # Valider hadith
                validation_result = await self.validator.validate_hadith(hadith_raw)
                
                self.stats["total_validated"] += 1
                
                yield emit("validation_progress", {
                    "current": i + 1,
                    "total": total_to_process,
                    "hadith_id": hadith_raw["id"],
                    "confidence": validation_result["confidence_score"],
                    "grade": validation_result["grade_normalized"]
                })
                
                # Décision: insertion auto ou review manuelle
                if validation_result["confidence_score"] >= self.CONFIDENCE_THRESHOLD:
                    # Insertion automatique
                    await self.db.insert_validated_hadith(
                        hadith_raw_id=hadith_raw["id"],
                        matn_ar=hadith_raw["matn_ar"],
                        translation_fr=validation_result["translation_fr"],
                        grade_normalized=validation_result["grade_normalized"],
                        scholar_verdict=validation_result["scholar_verdict"],
                        scholar_location=validation_result["scholar_location"],
                        confidence_score=validation_result["confidence_score"],
                        agent_isnad_output="{}",  # Placeholder
                        agent_ilal_output="{}",
                        agent_matn_output="{}",
                        agent_tarjih_output=json.dumps(validation_result)
                    )
                    
                    await self.db.mark_as_processed(hadith_raw["id"])
                    self.stats["total_inserted"] += 1
                    
                    yield emit("hadith_inserted", {
                        "hadith_id": hadith_raw["id"],
                        "confidence": validation_result["confidence_score"],
                        "grade": validation_result["grade_normalized"]
                    })
                else:
                    # Review manuelle
                    await self.db.insert_pending_review(
                        hadith_raw_id=hadith_raw["id"],
                        reason=f"Confiance {validation_result['confidence_score']:.1f}% < {self.CONFIDENCE_THRESHOLD}%",
                        confidence_score=validation_result["confidence_score"],
                        agent_outputs=json.dumps(validation_result)
                    )
                    
                    await self.db.mark_as_processed(hadith_raw["id"])
                    self.stats["total_pending_review"] += 1
                    
                    yield emit("hadith_pending_review", {
                        "hadith_id": hadith_raw["id"],
                        "confidence": validation_result["confidence_score"],
                        "reason": validation_result["reasoning"]
                    })
            
            except Exception as e:
                log.exception(f"[PIPELINE] Erreur traitement hadith ID={hadith_raw['id']}")
                self.stats["total_failed"] += 1
                
                yield emit("hadith_failed", {
                    "hadith_id": hadith_raw["id"],
                    "error": str(e)
                })
        
        yield emit("phase", {"phase": 2, "name": "VALIDATION", "status": "completed"})
        
        # Phase 3: Statistiques finales
        self.stats["end_time"] = datetime.now().isoformat()
        db_stats = await self.db.get_stats()
        
        yield emit("pipeline_complete", {
            "stats": {
                **self.stats,
                "db_stats": db_stats
            }
        })
    
    async def process_batch(
        self,
        start_id: int = 1,
        count: int = 1000,
        rate_limit: float = 2.0
    ) -> Dict[str, Any]:
        """Pipeline complet en mode batch (sans streaming).
        
        Returns:
            Statistiques finales
        """
        log.info(f"[PIPELINE] Démarrage batch: start_id={start_id}, count={count}")
        
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Phase 1: Harvesting
        harvester = HadithHarvester(start_id, count, rate_limit)
        harvest_stats = await harvester.harvest()
        self.stats["total_harvested"] = harvest_stats["total_success"]
        
        # Phase 2: Validation
        unprocessed = await self.db.get_unprocessed_hadiths(limit=count)
        
        for hadith_raw in unprocessed:
            try:
                validation_result = await self.validator.validate_hadith(hadith_raw)
                self.stats["total_validated"] += 1
                
                if validation_result["confidence_score"] >= self.CONFIDENCE_THRESHOLD:
                    await self.db.insert_validated_hadith(
                        hadith_raw_id=hadith_raw["id"],
                        matn_ar=hadith_raw["matn_ar"],
                        translation_fr=validation_result["translation_fr"],
                        grade_normalized=validation_result["grade_normalized"],
                        scholar_verdict=validation_result["scholar_verdict"],
                        scholar_location=validation_result["scholar_location"],
                        confidence_score=validation_result["confidence_score"],
                        agent_isnad_output="{}",
                        agent_ilal_output="{}",
                        agent_matn_output="{}",
                        agent_tarjih_output=json.dumps(validation_result)
                    )
                    self.stats["total_inserted"] += 1
                else:
                    await self.db.insert_pending_review(
                        hadith_raw_id=hadith_raw["id"],
                        reason=f"Confiance insuffisante",
                        confidence_score=validation_result["confidence_score"],
                        agent_outputs=json.dumps(validation_result)
                    )
                    self.stats["total_pending_review"] += 1
                
                await self.db.mark_as_processed(hadith_raw["id"])
            
            except Exception as e:
                log.exception(f"[PIPELINE] Erreur hadith ID={hadith_raw['id']}")
                self.stats["total_failed"] += 1
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        log.info(
            f"[PIPELINE] Terminé: "
            f"harvested={self.stats['total_harvested']}, "
            f"validated={self.stats['total_validated']}, "
            f"inserted={self.stats['total_inserted']}, "
            f"pending={self.stats['total_pending_review']}, "
            f"failed={self.stats['total_failed']}"
        )
        
        return self.stats