"""
Vérifie l'état des grades dans almizane.db
"""
import sqlite3
from pathlib import Path

DB = Path("backend/almizane.db")

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    # Total hadiths
    cur.execute("SELECT COUNT(*) FROM hadiths")
    total = cur.fetchone()[0]
    
    # Hadiths avec grade_final
    cur.execute("SELECT COUNT(*) FROM hadiths WHERE grade_final IS NOT NULL AND grade_final != ''")
    with_grade_final = cur.fetchone()[0]
    
    # Hadiths avec grade_synthese (nouveau système)
    cur.execute("SELECT COUNT(*) FROM hadiths WHERE grade_synthese IS NOT NULL")
    with_grade_synthese = cur.fetchone()[0]
    
    # Hadiths avec au moins un verdict dans ahkam
    cur.execute("""
        SELECT COUNT(DISTINCT hadith_id) 
        FROM ahkam
    """)
    with_ahkam = cur.fetchone()[0]
    
    # Distribution des grades existants
    cur.execute("""
        SELECT grade_final, COUNT(*) as cnt 
        FROM hadiths 
        WHERE grade_final IS NOT NULL AND grade_final != ''
        GROUP BY grade_final 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    grade_dist = cur.fetchall()
    
    print("=" * 60)
    print("ÉTAT DES GRADES - almizane.db")
    print("=" * 60)
    print(f"\nTotal hadiths : {total:,}")
    print(f"Avec grade_final : {with_grade_final:,} ({with_grade_final/total*100:.1f}%)")
    print(f"Avec grade_synthese : {with_grade_synthese:,} ({with_grade_synthese/total*100:.1f}%)")
    print(f"Avec verdicts (ahkam) : {with_ahkam:,} ({with_ahkam/total*100:.1f}%)")
    print(f"\nSans aucun grade : {total - with_grade_final:,}")
    
    print("\n" + "=" * 60)
    print("DISTRIBUTION DES GRADES EXISTANTS (TOP 10)")
    print("=" * 60)
    for grade, cnt in grade_dist:
        print(f"{grade:30} : {cnt:>6,} ({cnt/total*100:>5.1f}%)")
    
    # Exemples de hadiths sans grade
    print("\n" + "=" * 60)
    print("EXEMPLES DE HADITHS SANS GRADE (5 premiers)")
    print("=" * 60)
    cur.execute("""
        SELECT id, collection, numero_hadith, 
               SUBSTR(matn_ar, 1, 80) as matn_preview
        FROM hadiths 
        WHERE (grade_final IS NULL OR grade_final = '')
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"\nID: {row[0]}")
        print(f"Collection: {row[1]} #{row[2]}")
        print(f"Matn: {row[3]}...")
    
    conn.close()

if __name__ == "__main__":
    main()