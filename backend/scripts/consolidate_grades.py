"""
Phase 4 — Consolidation des verdicts (grade_synthese)
À partir de la table ahkam (plusieurs verdicts par hadith),
calcule un grade_synthese avec règles méthodologiques salafi.

Règles de priorité :
1. Si Bukhārī ou Muslim l'ont sorti dans leurs Sahih → sahih (prioritaire)
2. Si Albānī a tranché → son verdict fait foi pour Kutub al-Sittah hors Sahihayn
3. Conflit entre contemporains → trancher en faveur du plus strict sur le sanad
4. Si aucun verdict trouvé → grade_synthese = 'non_verifie'
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path("backend/almizane.db")

# Ordre de priorité (plus haut = plus prioritaire)
# Basé sur la méthodologie salafi : Sahihayn > Albani > autres muhaddithīn
PRIORITY = {
    # Sahihayn (priorité absolue)
    "البخاري": 100,
    "مسلم": 100,
    
    # Muhaddithīn contemporains salafi
    "الألباني": 90,
    "شعيب الأرناؤوط": 85,
    
    # Imams classiques du hadith
    "ابن حجر": 80,
    "ابن حجر العسقلاني": 80,
    "الذهبي": 80,
    "النووي": 80,
    "ابن القيم": 75,
    
    # Critiques du hadith classiques
    "الدارقطني": 75,
    "أبو حاتم الرازي": 70,
    "أبو زرعة الرازي": 70,
    "يحيى بن معين": 70,
    "الإمام أحمد": 70,
    "أحمد بن حنبل": 70,
    
    # Savants contemporains salafi
    "ابن باز": 70,
    "ابن عثيمين": 70,
    "مقبل الوادعي": 70,
    
    # Autres muhaddithīn
    "الترمذي": 65,
    "أبو داود": 65,
    "النسائي": 65,
    "ابن ماجه": 65,
    "ابن حبان": 65,
}

# Hiérarchie des grades (pour résoudre les conflits)
GRADE_HIERARCHY = {
    "sahih_li_dhatihi": 10,
    "sahih": 9,
    "sahih_li_ghayrihi": 8,
    "hasan_sahih": 7,
    "hasan_li_dhatihi": 6,
    "hasan": 5,
    "hasan_li_ghayrihi": 4,
    "daif": 3,
    "daif_jiddan": 2,
    "munkar": 1,
    "mawduʿ": 0,
    "la_yasihh": 0,
    "la_asla_lah": 0,
    "batil": 0,
    "kadhib": 0,
}

def consolidate(verdicts):
    """
    Consolide plusieurs verdicts en un grade_synthese unique
    Retourne (grade, confidence)
    """
    if not verdicts:
        return ("non_verifie", 0.0)
    
    # Tri par priorité du critic (plus haute priorité en premier)
    verdicts.sort(key=lambda v: PRIORITY.get(v["critic"], 10), reverse=True)
    
    # Cas spécial : si Bukhari ou Muslim ont tranché, c'est sahih
    for v in verdicts:
        if v["critic"] in ["البخاري", "مسلم"]:
            if v["hukm_class"] in ["sahih", "sahih_li_dhatihi"]:
                return ("sahih", 1.0)
    
    # Sinon, prendre le verdict du plus prioritaire
    top = verdicts[0]
    top_grade = top["hukm_class"]
    
    # Si le top est "unknown", chercher le premier verdict connu
    if top_grade == "unknown":
        for v in verdicts:
            if v["hukm_class"] != "unknown":
                top_grade = v["hukm_class"]
                break
    
    # Si toujours unknown, retourner non_verifie
    if top_grade == "unknown":
        return ("non_verifie", 0.0)
    
    # Calculer la confidence basée sur la concordance
    # Compter combien de verdicts sont d'accord (même grade ou grade proche)
    top_hierarchy = GRADE_HIERARCHY.get(top_grade, 5)
    agree = 0
    
    for v in verdicts:
        v_grade = v["hukm_class"]
        if v_grade == "unknown":
            continue
        v_hierarchy = GRADE_HIERARCHY.get(v_grade, 5)
        
        # Accord si même grade ou différence ≤ 2 niveaux
        if abs(top_hierarchy - v_hierarchy) <= 2:
            agree += 1
    
    # Confidence = ratio d'accord parmi les verdicts non-unknown
    non_unknown = sum(1 for v in verdicts if v["hukm_class"] != "unknown")
    confidence = agree / non_unknown if non_unknown > 0 else 0.0
    
    return (top_grade, round(confidence, 2))

def main():
    """Point d'entrée principal"""
    print("="*60)
    print("CONSOLIDATION DES GRADES (Phase 4)")
    print("="*60)
    
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Récupérer tous les hadiths avec leurs verdicts
    cur.execute("""
      SELECT h.id,
             json_group_array(json_object(
               'critic', s.name_ar,
               'hukm_class', a.hukm_class
             )) as verdicts_json
      FROM hadiths h
      JOIN ahkam a ON a.hadith_id = h.id
      JOIN hukm_sources s ON s.id = a.source_id
      GROUP BY h.id
    """)
    
    rows = cur.fetchall()
    print(f"\n📊 Hadiths avec verdicts : {len(rows):,}")
    
    updated = 0
    stats = {}
    
    for row in rows:
        hid = row["id"]
        verdicts = json.loads(row["verdicts_json"])
        
        grade, conf = consolidate(verdicts)
        
        # Compter les stats
        stats[grade] = stats.get(grade, 0) + 1
        
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
    print("\n" + "="*60)

if __name__ == "__main__":
    main()