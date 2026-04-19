"""
Normalise le matn arabe pour la recherche :
- Supprime les diacritiques (tashkīl)
- Unifie alif (ا/أ/إ/آ → ا), ya (ي/ى → ي), ta marbuta (ة/ه → ه)
- Supprime le tatweel (ـ)
- Peuple matn_ar_normalized
- Rafraîchit l'index FTS5
"""
import re
import sqlite3
from pathlib import Path

DB = Path("backend/almizane.db")

DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")

def normalize(text: str) -> str:
    if not text:
        return ""
    text = DIACRITICS.sub("", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ئ", "ي")
    text = text.replace("ؤ", "و")
    text = text.replace("ة", "ه")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def main():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    cur = conn.cursor()

    cur.execute("SELECT id, matn_ar FROM hadiths WHERE matn_ar_normalized IS NULL")
    rows = cur.fetchall()
    print(f"À normaliser : {len(rows)}")

    for i, (hid, matn) in enumerate(rows):
        cur.execute(
            "UPDATE hadiths SET matn_ar_normalized = ? WHERE id = ?",
            (normalize(matn or ""), hid),
        )
        if i % 5000 == 0:
            conn.commit()
            print(f"  {i}/{len(rows)}")

    conn.commit()

    # Reconstruire l'index FTS
    print("Reconstruction de l'index FTS...")
    cur.execute("INSERT INTO hadiths_fts(hadiths_fts) VALUES('rebuild');")
    conn.commit()
    conn.close()
    print("✅ Normalisation + FTS reconstruits")

if __name__ == "__main__":
    main()