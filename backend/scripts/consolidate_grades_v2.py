"""
Phase 4 v2 — Consolidation des verdicts selon les règles classiques
Conforme au BRIEF v2 - PARTIE D

Règles de pondération basées sur Ibn Ḥajar (Nuzhat al-Naẓar) + Ibn Rajab (Sharḥ ʿIlal) :

1. **Awlawiyyat al-mutaqaddimīn** : en cas d'ikhtilāf entre mutaqaddim et mutaʾakhkhir
   sur la même ʿillah, le mutaqaddim qui connaissait le rāwī personnellement est prioritaire.
2. **Mufassar muqaddam ʿalā mujmal** : un jarḥ expliqué prime sur un taʿdīl général.
3. **Présence dans Ṣaḥīḥayn** = ṣaḥīḥ définitif (pas de re-debate).
4. **Ijmāʿ al-muḥaddithīn** sur un jugement = verdict absolu.
5. **Pour les contemporains** : priorité Albānī > Shuʿayb al-Arnaʾūṭ > Muqbil > autres.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path("backend/almizane.db")

def _check_ijmaʿ(verdicts):
    """Vérifie s'il y a consensus (ijmāʿ) entre les muḥaddithīn"""
    if len(verdicts) < 3:
        return None
    
    classes = {v["hukm_class"] for v in verdicts if v["hukm_class"] != "unknown"}
    
    # Ijmāʿ = tous d'accord sur la même classe
    if len(classes) == 1:
        return verdicts[0]
    
    return None

def _prioritize_mutaqaddim(verdicts):
    """Priorité aux mutaqaddimīn sur les questions de ʿilal"""
    muta = [v for v in verdicts if v.get("tabaqah") == "mutaqaddim"]
    
    if not muta:
        return None
    
    # S'il y a consensus entre mutaqaddimīn
    classes = {v["hukm_class"] for v in muta if v["hukm_class"] != "unknown"}
    
    if len(classes) == 1:
        return muta[0]
    
    return None

def _weighted_majority(verdicts):
    """Calcul de la majorité pondérée par reliability_weight"""
    scores = {}
    
    for v in verdicts:
        cls = v["hukm_class"]
        if cls == "unknown":
            continue
        
        weight = v.get("weight", 0.5)
        scores[cls] = scores.get(cls, 0) + weight
    
    if not scores:
        return None
    
    best_cls = max(scores, key=scores.get)
    total_weight = sum(scores.values())
    confidence = scores[best_cls] / total_weight if total_weight > 0 else 0.0
    
    return {
        "hukm_class": best_cls,
        "confidence": confidence
    }

# Règles cascadées (ordre = priorité)
RULES = [
    # Règle 1 : Sahihayn (priorité absolue)
    lambda verdicts: next(
        (v for v in verdicts 
         if v["critic"] in ("البخاري", "مسلم") 
         and v["hukm_class"] in ("sahih", "sahih_li_dhatihi")),
        None
    ),
    
    # Règle 2 : Ijmāʿ (consensus complet)
    _check_ijmaʿ,
    
    # Règle 3 : Priorité mutaqaddimīn sur ʿilal
    _prioritize_mutaqaddim,
    
    # Règle 4 : Priorité Albānī pour les hadiths hors Ṣaḥīḥayn
    lambda verdicts: next(
        (v for v in verdicts 
         if v["critic"] == "محمد ناصر الدين الألباني"),
        None
    ),
    
    # Règle 5 : Majorité pondérée
    _weighted_majority,
]

def consolidate(verdicts):
    """
    Consolide plusieurs verdicts en un grade_synthese unique
    Retourne dict avec grade, confidence, applied_rule
    """
    if not verdicts:
        return {
            "grade": "non_verifie",
            "confidence": 0.0,
            "applied_rule": None
        }
    
    # Appliquer les règles dans l'ordre
    for i, rule in enumerate(RULES):
        result = rule(verdicts)
        
        if result:
            return {
                "grade": result["hukm_class"],
                "confidence": result.get("confidence", 0.95),
                "applied_rule": f"rule_{i+1}",
                "rule_name": [
                    "sahihayn",
                    "ijmaʿ",
                    "mutaqaddimin",
                    "albani",
                    "weighted_majority"
                ][i]
            }
    
    # Aucune règle n'a tranché = divergence
    return {
        "grade": "mukhtalaf_fih",
        "confidence": 0.5,
        "applied_rule": "divergence"
    }

def main():
    """Point d'entrée principal"""
    print("="*70)
    print("CONSOLIDATION DES GRADES v2 (Règles Classiques)")
    print("="*70)
    
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Récupérer tous les hadiths avec leurs verdicts
    cur.execute("""
      SELECT h.id,
             json_group_array(json_object(
               'critic', s.name_ar,
               'hukm_class', a.hukm_class,
               'tabaqah', s.tabaqah,
               'weight', s.reliability_weight
             )) AS verdicts_json
      FROM hadiths h
      JOIN ahkam a ON a.hadith_id = h.id
      JOIN hukm_sources s ON s.id = a.source_id
      GROUP BY h.id
    """)
    
    rows = cur.fetchall()
    print(f"\n📊 Hadiths avec verdicts : {len(rows):,}")
    
    updated = 0
    stats = {}
    rule_stats = {}
    
    for row in rows:
        hid = row["id"]
        verdicts = json.loads(row["verdicts_json"])
        
        result = consolidate(verdicts)
        grade = result["grade"]
        conf = result["confidence"]
        rule = result.get("rule_name", "unknown")
        
        # Compter les stats
        stats[grade] = stats.get(grade, 0) + 1
        rule_stats[rule] = rule_stats.get(rule, 0) + 1
        
        # Mettre à jour la base
        cur.execute("""
            UPDATE hadiths 
            SET grade_synthese = ?, 
                grade_confidence = ?, 
                verified_at = datetime('now')
            WHERE id = ?
        """, (grade, conf, hid))
        
        updated += 1
        
        if updated % 1000 == 0:
            conn.commit()
            print(f"  Progression : {updated:,}/{len(rows):,}")
    
    conn.commit()
    
    print(f"\n✅ Consolidation terminée : {updated:,} hadiths mis à jour")
    
    print(f"\n📊 Répartition des grades :")
    for grade, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / updated * 100) if updated > 0 else 0
        print(f"  • {grade}: {count:,} ({pct:.1f}%)")
    
    print(f"\n📋 Règles appliquées :")
    for rule, count in sorted(rule_stats.items(), key=lambda x: x[1], reverse=True):
        pct = (count / updated * 100) if updated > 0 else 0
        print(f"  • {rule}: {count:,} ({pct:.1f}%)")
    
    # Statistiques de confidence
    cur.execute("""
        SELECT 
            AVG(grade_confidence) as avg_conf,
            MIN(grade_confidence) as min_conf,
            MAX(grade_confidence) as max_conf
        FROM hadiths
        WHERE grade_synthese IS NOT NULL AND grade_synthese != 'non_verifie'
    """)
    conf_stats = cur.fetchone()
    
    if conf_stats and conf_stats["avg_conf"]:
        print(f"\n📈 Statistiques de confidence :")
        print(f"  • Moyenne : {conf_stats['avg_conf']:.2f}")
        print(f"  • Min : {conf_stats['min_conf']:.2f}")
        print(f"  • Max : {conf_stats['max_conf']:.2f}")
    
    conn.close()
    print("\n" + "="*70)

if __name__ == "__main__":
    main()