# ⚠️ RÈGLE SUPRÊME — PRIORITÉ ABSOLUE
# G est le seul décideur. Si une règle bloque → signaler : (1) quelle règle (2) pourquoi (3) proposition. G valide. Aucun blocage silencieux.
# Contrainte absolue : conformité manhaj Salaf — al-Albānī, Ibn Bāz, Ibn ʿUthaymīn.
"""
Enrichissement ciblé des zones 03, 11, 19, 22, 30.

Règles:
- UPDATE uniquement (aucun INSERT).
- Matching strict: (book_name_fr, hadith_number normalisé en int).
- Sources locales: backend/data/dumps/fawazahmed0_fr_dump.json + hadeethenc_full_dump.json.

Usage:
  python backend/scripts/enrich_zones_0311192230.py
  python backend/scripts/enrich_zones_0311192230.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "backend" / "database" / "almizan_v7.db"
FAWAZ_PATH = ROOT / "backend" / "data" / "dumps" / "fawazahmed0_fr_dump.json"
HADEETHENC_PATH = ROOT / "backend" / "data" / "dumps" / "hadeethenc_full_dump.json"

TARGET_ZONES = (3, 11, 19, 22, 30)

FAWAZ_BOOK_MAP = {
	"fra-bukhari": "Sahih al-Bukhari",
	"fra-muslim": "Sahih Muslim",
	"fra-nasai": "Sunan an-Nasai",
	"fra-abudawud": "Sunan Abu Dawud",
	"fra-ibnmajah": "Sunan Ibn Majah",
	"fra-malik": "Muwatta Malik",
	"fra-nawawi": "40 Hadiths de Nawawi",
	"fra-dehlawi": "40 Hadiths de Dehlawi",
	"fra-qudsi": "40 Hadiths Qudsi",
}

REF_BOOK_PATTERNS = [
	(r"bukhari", "Sahih al-Bukhari"),
	(r"muslim", "Sahih Muslim"),
	(r"abu\s*dawud|ab[ou]\s*dawud", "Sunan Abu Dawud"),
	(r"nas[ai]i|an[-\s]?nasai", "Sunan an-Nasai"),
	(r"ibn\s*majah|ibn\s*maja", "Sunan Ibn Majah"),
	(r"muwatta|malik", "Muwatta Malik"),
]


def normalize_num(value) -> int | None:
	try:
		return int(str(value).strip())
	except (ValueError, TypeError):
		return None


def normalize_grade(value: str | None) -> str | None:
	if not value:
		return None
	v = value.strip().lower()
	if "sahih" in v:
		return "Sahih"
	if "hasan" in v:
		return "Hasan"
	if "maw" in v or "forg" in v:
		return "Mawdu'"
	if "munkar" in v:
		return "Munkar"
	if "da" in v or "faible" in v:
		return "Da'if"
	return None


def extract_fawaz_grade(grades_field) -> str | None:
	if not grades_field:
		return None
	if isinstance(grades_field, str):
		return grades_field.strip() or None
	if isinstance(grades_field, list) and grades_field:
		first = grades_field[0]
		if isinstance(first, dict):
			return first.get("grade") or None
		return str(first) or None
	return None


def extract_fawaz_albani(grades_field) -> str | None:
	if not isinstance(grades_field, list):
		return None
	for g in grades_field:
		if not isinstance(g, dict):
			continue
		name = str(g.get("name") or "").lower()
		if "albani" in name or "al-albani" in name:
			return g.get("grade") or None
	return None


def load_fawaz_index(path: Path) -> dict[tuple[str, int], dict]:
	raw = json.loads(path.read_text(encoding="utf-8"))
	out: dict[tuple[str, int], dict] = {}

	for fawaz_key, book_data in raw.items():
		book = FAWAZ_BOOK_MAP.get(fawaz_key)
		if not book:
			continue
		hadiths = book_data.get("hadiths", []) if isinstance(book_data, dict) else book_data
		if not isinstance(hadiths, list):
			continue
		for h in hadiths:
			if not isinstance(h, dict):
				continue
			num = normalize_num(h.get("hadithnumber") or h.get("number"))
			if num is None:
				continue
			out[(book, num)] = {
				"fr_text": (h.get("text") or "").strip() or None,
				"grade": normalize_grade(extract_fawaz_grade(h.get("grades"))),
				"albani": normalize_grade(extract_fawaz_albani(h.get("grades"))),
				"source": "fawazahmed0",
			}
	return out


def parse_hadeethenc_reference(reference: str | None) -> tuple[str, int] | None:
	if not reference or not isinstance(reference, str):
		return None
	ref = reference.lower()
	book = None
	for pat, name in REF_BOOK_PATTERNS:
		if re.search(pat, ref):
			book = name
			break
	if not book:
		return None

	num_match = re.search(r"(?:n[°o\.]?|no\.?|#)\s*(\d{1,6})", ref)
	if not num_match:
		num_match = re.search(r"\b(\d{1,6})\b", ref)
	if not num_match:
		return None

	num = normalize_num(num_match.group(1))
	if num is None:
		return None
	return (book, num)


def load_hadeethenc_index(path: Path) -> dict[tuple[str, int], dict]:
	raw = json.loads(path.read_text(encoding="utf-8"))
	hadiths = raw.get("hadiths", []) if isinstance(raw, dict) else []
	out: dict[tuple[str, int], dict] = {}

	for h in hadiths:
		if not isinstance(h, dict):
			continue
		key = parse_hadeethenc_reference(h.get("reference"))
		if not key:
			continue
		out[key] = {
			"fr_text": (h.get("body") or "").strip() or None,
			"fr_summary": (h.get("title") or "").strip() or None,
			"fr_explanation": (h.get("explanation") or "").strip() or None,
			"grade": normalize_grade(h.get("grade")),
			"takhrij": (h.get("reference") or "").strip() or None,
			"source": "hadeethenc",
		}
	return out


def run(apply: bool) -> None:
	print("=" * 72)
	print(f"  enrich_zones_0311192230.py — mode: {'APPLY' if apply else 'DRY-RUN'}")
	print(f"  DB       : {DB_PATH}")
	print(f"  Fawaz    : {FAWAZ_PATH}")
	print(f"  HadeethEnc: {HADEETHENC_PATH}")
	print(f"  Date     : {datetime.now():%Y-%m-%d %H:%M:%S}")
	print("=" * 72)

	fawaz = load_fawaz_index(FAWAZ_PATH)
	hadeethenc = load_hadeethenc_index(HADEETHENC_PATH)
	print(f"[1/3] Index Fawaz chargé      : {len(fawaz):,} clés")
	print(f"[1/3] Index HadeethEnc chargé : {len(hadeethenc):,} clés (book+hadith_number)")

	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()

	placeholders = ",".join(["?"] * len(TARGET_ZONES))
	cur.execute(
		f"""
		SELECT id, zone_id, book_name_fr, hadith_number,
			   fr_text, fr_explanation, fr_summary,
			   grade_primary, grade_albani,
			   takhrij, source_api
		FROM entries
		WHERE zone_id IN ({placeholders})
		""",
		TARGET_ZONES,
	)
	rows = cur.fetchall()
	print(f"[2/3] Entrées DB dans zones cibles ({TARGET_ZONES}) : {len(rows):,}")

	stats = {
		"matched_fawaz": 0,
		"matched_hadeethenc": 0,
		"updates": 0,
		"upd_fr_text": 0,
		"upd_fr_explanation": 0,
		"upd_fr_summary": 0,
		"upd_grade": 0,
		"upd_albani": 0,
		"upd_takhrij": 0,
		"upd_source_api": 0,
	}
	updates = []

	for r in rows:
		num = normalize_num(r["hadith_number"])
		if num is None:
			continue

		key = (r["book_name_fr"], num)
		f = fawaz.get(key)
		h = hadeethenc.get(key)
		if f:
			stats["matched_fawaz"] += 1
		if h:
			stats["matched_hadeethenc"] += 1
		if not f and not h:
			continue

		cur_fr_text = (r["fr_text"] or "").strip()
		cur_fr_expl = (r["fr_explanation"] or "").strip()
		cur_fr_sum = (r["fr_summary"] or "").strip()
		cur_grade = (r["grade_primary"] or "").strip()
		cur_albani = (r["grade_albani"] or "").strip()
		cur_takhrij = (r["takhrij"] or "").strip()
		cur_source_api = (r["source_api"] or "").strip()

		new_fr_text = None if cur_fr_text else ((f or {}).get("fr_text") or (h or {}).get("fr_text"))
		new_fr_expl = None if cur_fr_expl else ((h or {}).get("fr_explanation"))
		new_fr_sum = None if cur_fr_sum else ((h or {}).get("fr_summary"))
		new_grade = None if cur_grade else ((f or {}).get("grade") or (h or {}).get("grade"))
		new_albani = None if cur_albani else ((f or {}).get("albani"))
		new_takhrij = None if cur_takhrij else ((h or {}).get("takhrij"))

		new_source_api = None
		if not cur_source_api and any([new_fr_text, new_fr_expl, new_fr_sum, new_grade, new_albani, new_takhrij]):
			if f:
				new_source_api = "fawazahmed0"
			elif h:
				new_source_api = "hadeethenc"

		if not any([new_fr_text, new_fr_expl, new_fr_sum, new_grade, new_albani, new_takhrij, new_source_api]):
			continue

		if new_fr_text:
			stats["upd_fr_text"] += 1
		if new_fr_expl:
			stats["upd_fr_explanation"] += 1
		if new_fr_sum:
			stats["upd_fr_summary"] += 1
		if new_grade:
			stats["upd_grade"] += 1
		if new_albani:
			stats["upd_albani"] += 1
		if new_takhrij:
			stats["upd_takhrij"] += 1
		if new_source_api:
			stats["upd_source_api"] += 1

		updates.append(
			{
				"id": r["id"],
				"fr_text": new_fr_text,
				"fr_explanation": new_fr_expl,
				"fr_summary": new_fr_sum,
				"grade_primary": new_grade,
				"grade_albani": new_albani,
				"takhrij": new_takhrij,
				"source_api": new_source_api,
			}
		)

	stats["updates"] = len(updates)

	print("[3/3] Résultat matching/enrichissement")
	print(f"      Match Fawaz        : {stats['matched_fawaz']:>8,}")
	print(f"      Match HadeethEnc   : {stats['matched_hadeethenc']:>8,}")
	print(f"      Updates préparés   : {stats['updates']:>8,}")
	print(f"      -> fr_text         : {stats['upd_fr_text']:>8,}")
	print(f"      -> fr_explanation  : {stats['upd_fr_explanation']:>8,}")
	print(f"      -> fr_summary      : {stats['upd_fr_summary']:>8,}")
	print(f"      -> grade_primary   : {stats['upd_grade']:>8,}")
	print(f"      -> grade_albani    : {stats['upd_albani']:>8,}")
	print(f"      -> takhrij         : {stats['upd_takhrij']:>8,}")
	print(f"      -> source_api      : {stats['upd_source_api']:>8,}")

	if not updates:
		print("\nAucune mise à jour à appliquer.")
		conn.close()
		return

	if not apply:
		print("\nAperçu (5 premières updates):")
		for u in updates[:5]:
			changed = [k for k, v in u.items() if k != "id" and v is not None]
			print(f"  id={u['id']!r} champs={changed}")
		print("\n[DRY-RUN] Aucune écriture effectuée. Relancer avec --apply.")
		conn.close()
		return

	applied = 0
	conn.execute("BEGIN")
	try:
		for u in updates:
			fields = []
			params = []
			for field in (
				"fr_text",
				"fr_explanation",
				"fr_summary",
				"grade_primary",
				"grade_albani",
				"takhrij",
				"source_api",
			):
				val = u.get(field)
				if val is not None:
					fields.append(f"{field} = ?")
					params.append(val)

			if not fields:
				continue

			fields.append("updated_at = ?")
			params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			params.append(u["id"])
			sql = f"UPDATE entries SET {', '.join(fields)} WHERE id = ?"
			conn.execute(sql, params)
			applied += 1

		conn.commit()
		print(f"\n✓ APPLY terminé: {applied:,} rows mises à jour.")
	except Exception as exc:
		conn.rollback()
		print(f"\n✗ ERREUR: rollback effectué: {exc}")
		raise
	finally:
		conn.close()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Enrichit les zones 03/11/19/22/30 depuis dumps locaux (Fawaz + HadeethEnc)."
	)
	parser.add_argument("--apply", action="store_true", default=False, help="Appliquer les UPDATE")
	args = parser.parse_args()
	run(apply=args.apply)

