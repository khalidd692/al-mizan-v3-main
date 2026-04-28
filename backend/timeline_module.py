"""
Module de Confrontation - Timeline de la Science
Affiche l'évolution des avis sur un hadith à travers les siècles
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

class TimelineModule:
    """Génère une timeline chronologique des avis de savants sur un hadith"""
    
    # Classification des époques (en années hégiennes)
    EPOCHS = {
        "anciens": {
            "name": "Les Anciens (Salaf)",
            "range": (0, 300),
            "description": "Les trois premières générations bénis"
        },
        "medievaux": {
            "name": "Les Médiévaux",
            "range": (300, 900),
            "description": "L'âge d'or de la science du hadith"
        },
        "contemporains": {
            "name": "Les Contemporains",
            "range": (900, 1500),
            "description": "Les savants modernes"
        }
    }
    
    def __init__(self, db_path: str = "backend/database/al_mizan_v7.db"):
        self.db_path = db_path
    
    def get_hadith_timeline(self, hadith_id: int) -> Dict:
        """
        Récupère la timeline complète d'un hadith avec tous les avis
        
        Returns:
            {
                "hadith": {...},
                "timeline": {
                    "anciens": [...],
                    "medievaux": [...],
                    "contemporains": [...]
                },
                "consensus": {...},
                "divergences": [...]
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Récupérer le hadith
        cursor.execute("""
            SELECT * FROM entries WHERE id = ?
        """, (hadith_id,))
        hadith = dict(cursor.fetchone())
        
        # 2. Récupérer tous les avis avec les infos des savants
        cursor.execute("""
            SELECT 
                v.grade,
                v.reasoning,
                v.verified_at,
                a.name,
                a.full_name,
                a.birth_year_hijri,
                a.death_year_hijri,
                a.school,
                a.specialization,
                a.reliability_score
            FROM validations v
            JOIN authorities a ON v.authority_id = a.id
            WHERE v.entry_id = ?
            ORDER BY a.death_year_hijri ASC
        """, (hadith_id,))
        
        validations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # 3. Organiser par époque
        timeline = {
            "anciens": [],
            "medievaux": [],
            "contemporains": []
        }
        
        for validation in validations:
            death_year = validation['death_year_hijri']
            epoch = self._classify_epoch(death_year)
            
            timeline[epoch].append({
                "scholar": {
                    "name": validation['name'],
                    "full_name": validation['full_name'],
                    "years": f"{validation['birth_year_hijri']}-{validation['death_year_hijri']}H",
                    "school": validation['school'],
                    "specialization": validation['specialization'],
                    "reliability": validation['reliability_score']
                },
                "ruling": {
                    "grade": validation['grade'],
                    "reasoning": validation['reasoning'],
                    "date": validation['verified_at']
                }
            })
        
        # 4. Analyser le consensus
        consensus = self._analyze_consensus(validations)
        
        # 5. Identifier les divergences
        divergences = self._identify_divergences(validations)
        
        return {
            "hadith": hadith,
            "timeline": timeline,
            "consensus": consensus,
            "divergences": divergences,
            "metadata": {
                "total_scholars": len(validations),
                "epochs_covered": [k for k, v in timeline.items() if v],
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def _classify_epoch(self, death_year: int) -> str:
        """Classifie un savant dans une époque selon son année de décès"""
        for epoch, data in self.EPOCHS.items():
            if data["range"][0] <= death_year < data["range"][1]:
                return epoch
        return "contemporains"  # Par défaut
    
    def _analyze_consensus(self, validations: List[Dict]) -> Dict:
        """Analyse s'il y a consensus entre les savants"""
        grades = [v['grade'] for v in validations]
        
        # Compter les occurrences
        grade_counts = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Trouver le grade majoritaire
        majority_grade = max(grade_counts, key=grade_counts.get)
        majority_count = grade_counts[majority_grade]
        total = len(grades)
        
        consensus_level = majority_count / total if total > 0 else 0
        
        return {
            "exists": consensus_level >= 0.75,  # 75% = consensus
            "grade": majority_grade,
            "percentage": round(consensus_level * 100, 1),
            "distribution": grade_counts,
            "interpretation": self._interpret_consensus(consensus_level)
        }
    
    def _interpret_consensus(self, level: float) -> str:
        """Interprète le niveau de consensus"""
        if level >= 0.95:
            return "Consensus unanime (إجماع)"
        elif level >= 0.75:
            return "Consensus fort (اتفاق)"
        elif level >= 0.60:
            return "Majorité (جمهور)"
        else:
            return "Divergence (اختلاف)"
    
    def _identify_divergences(self, validations: List[Dict]) -> List[Dict]:
        """Identifie les points de divergence entre savants"""
        divergences = []
        grades = {}
        
        # Grouper par grade
        for v in validations:
            grade = v['grade']
            if grade not in grades:
                grades[grade] = []
            grades[grade].append(v)
        
        # Si plus d'un grade, il y a divergence
        if len(grades) > 1:
            for grade, scholars in grades.items():
                divergences.append({
                    "position": grade,
                    "scholars": [s['name'] for s in scholars],
                    "count": len(scholars),
                    "main_reasoning": scholars[0]['reasoning'] if scholars else None
                })
        
        return divergences
    
    def get_scholar_profile(self, scholar_name: str) -> Optional[Dict]:
        """Récupère le profil complet d'un savant"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM authorities WHERE name = ? OR full_name = ?
        """, (scholar_name, scholar_name))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    def compare_scholars(self, hadith_id: int, scholar1: str, scholar2: str) -> Dict:
        """Compare les avis de deux savants sur un hadith"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                v.grade,
                v.reasoning,
                a.name,
                a.full_name,
                a.school,
                a.specialization
            FROM validations v
            JOIN authorities a ON v.authority_id = a.id
            WHERE v.entry_id = ? AND (a.name = ? OR a.name = ?)
        """, (hadith_id, scholar1, scholar2))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if len(results) != 2:
            return {"error": "Les deux savants n'ont pas d'avis sur ce hadith"}
        
        return {
            "scholar1": results[0],
            "scholar2": results[1],
            "agreement": results[0]['grade'] == results[1]['grade'],
            "difference": self._explain_difference(results[0], results[1])
        }
    
    def _explain_difference(self, ruling1: Dict, ruling2: Dict) -> Optional[str]:
        """Explique la différence entre deux avis"""
        if ruling1['grade'] == ruling2['grade']:
            return None
        
        return f"{ruling1['name']} juge '{ruling1['grade']}' tandis que {ruling2['name']} juge '{ruling2['grade']}'"

# Fonction utilitaire pour l'API
def get_timeline_for_hadith(hadith_id: int) -> Dict:
    """Point d'entrée principal pour l'API"""
    module = TimelineModule()
    return module.get_hadith_timeline(hadith_id)

if __name__ == "__main__":
    # Test du module
    module = TimelineModule()
    
    # Tester avec le premier hadith
    timeline = module.get_hadith_timeline(1)
    
    print("=== TIMELINE DE LA SCIENCE ===")
    print(f"\nHadith: {timeline['hadith']['arabic_text'][:100]}...")
    print(f"\nTotal savants: {timeline['metadata']['total_scholars']}")
    print(f"Consensus: {timeline['consensus']['interpretation']} ({timeline['consensus']['percentage']}%)")
    
    for epoch in ['anciens', 'medievaux', 'contemporains']:
        scholars = timeline['timeline'][epoch]
        if scholars:
            print(f"\n{TimelineModule.EPOCHS[epoch]['name']} ({len(scholars)} savants):")
            for s in scholars:
                print(f"  - {s['scholar']['name']} ({s['scholar']['years']}): {s['ruling']['grade']}")