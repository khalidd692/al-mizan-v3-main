"""
API Endpoints pour le Module de Confrontation - Timeline de la Science
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from timeline_module import TimelineModule
import uvicorn

app = FastAPI(title="Al-Mīzān Timeline API", version="1.0.0")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instance du module timeline
timeline_module = TimelineModule()

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "name": "Al-Mīzān Timeline API",
        "version": "1.0.0",
        "description": "Module de Confrontation - Timeline de la Science",
        "endpoints": {
            "timeline": "/api/timeline/{hadith_id}",
            "scholar": "/api/scholar/{scholar_name}",
            "compare": "/api/compare/{hadith_id}/{scholar1}/{scholar2}"
        }
    }

@app.get("/api/timeline/{hadith_id}")
async def get_timeline(hadith_id: int):
    """
    Récupère la timeline complète d'un hadith avec tous les avis de savants
    
    Args:
        hadith_id: ID du hadith dans la base de données
        
    Returns:
        Timeline complète avec époques, consensus et divergences
    """
    try:
        timeline = timeline_module.get_hadith_timeline(hadith_id)
        return timeline
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Hadith non trouvé: {str(e)}")

@app.get("/api/scholar/{scholar_name}")
async def get_scholar_profile(scholar_name: str):
    """
    Récupère le profil complet d'un savant
    
    Args:
        scholar_name: Nom du savant (arabe ou translittéré)
        
    Returns:
        Profil complet du savant avec biographie et statistiques
    """
    profile = timeline_module.get_scholar_profile(scholar_name)
    
    if not profile:
        raise HTTPException(status_code=404, detail=f"Savant non trouvé: {scholar_name}")
    
    return profile

@app.get("/api/compare/{hadith_id}/{scholar1}/{scholar2}")
async def compare_scholars(hadith_id: int, scholar1: str, scholar2: str):
    """
    Compare les avis de deux savants sur un hadith spécifique
    
    Args:
        hadith_id: ID du hadith
        scholar1: Nom du premier savant
        scholar2: Nom du second savant
        
    Returns:
        Comparaison détaillée des deux avis
    """
    try:
        comparison = timeline_module.compare_scholars(hadith_id, scholar1, scholar2)
        
        if "error" in comparison:
            raise HTTPException(status_code=404, detail=comparison["error"])
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de comparaison: {str(e)}")

@app.get("/health")
async def health_check():
    """Vérification de santé de l'API"""
    return {
        "status": "healthy",
        "service": "timeline-api",
        "database": "connected"
    }

if __name__ == "__main__":
    print("🚀 Démarrage de l'API Timeline...")
    print("📍 URL: http://localhost:8001")
    print("📚 Documentation: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )