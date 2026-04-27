#!/usr/bin/env python3
"""
Spider pour récupérer toutes les traductions françaises depuis fawazahmed0/hadith-api.
Sauvegarde dans fawazahmed0_fr_dump.json avec checkpoint toutes les 500 entrées.
NE TOUCHE PAS à almizane.db.
"""

import json
import time
import urllib.request
import urllib.error
import os
import sys

BASE_URL = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions"

FR_EDITIONS = [
    "fra-abudawud",
    "fra-bukhari",
    "fra-dehlawi",
    "fra-ibnmajah",
    "fra-malik",
    "fra-muslim",
    "fra-nasai",
    "fra-nawawi",
    "fra-qudsi",
]

OUTPUT_FILE = "/home/user/al-mizan-v3-main/fawazahmed0_fr_dump.json"
CHECKPOINT_FILE = "/home/user/al-mizan-v3-main/fawazahmed0_fr_checkpoint.json"
CHECKPOINT_EVERY = 500
DELAY = 1.0  # secondes entre appels API

# Éditions dont la méthodologie doit être vérifiée avant ingestion
FLAG_EDITIONS = {"fra-nawawi", "fra-dehlawi"}


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "al-mizan-spider/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"  [HTTP {e.code}] {url}")
            if e.code == 404:
                return None
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"  [ERR] {url} -> {e}")
            time.sleep(2 ** attempt)
    return None


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_editions": [], "total_hadiths": 0}


def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def save_dump(all_data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    size_mb = os.path.getsize(OUTPUT_FILE) / 1024 / 1024
    print(f"  [DUMP] {OUTPUT_FILE} — {size_mb:.1f} MB")


def main():
    checkpoint = load_checkpoint()
    done_editions = set(checkpoint["done_editions"])
    total_hadiths = checkpoint["total_hadiths"]

    # Charge le dump existant si présent
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        print(f"[RESUME] Dump existant chargé : {len(all_data)} entrées")
    else:
        all_data = {}

    hadiths_since_checkpoint = 0

    for edition in FR_EDITIONS:
        if edition in done_editions:
            print(f"[SKIP] {edition} déjà téléchargé")
            continue

        print(f"\n[FETCH] {edition} ...")
        url = f"{BASE_URL}/{edition}.json"
        data = fetch_json(url)
        time.sleep(DELAY)

        if data is None:
            print(f"  [WARN] Impossible de récupérer {edition}, on passe.")
            continue

        # Structure typique : {"metadata": {...}, "hadiths": [...]}
        hadiths = data.get("hadiths", [])
        metadata = data.get("metadata", {})

        print(f"  -> {len(hadiths)} hadiths trouvés")

        entry = {
            "metadata": metadata,
            "hadiths": hadiths,
        }
        if edition in FLAG_EDITIONS:
            entry["flag"] = "methodologie_a_verifier"

        all_data[edition] = entry

        total_hadiths += len(hadiths)
        hadiths_since_checkpoint += len(hadiths)
        done_editions.add(edition)

        print(f"  [OK] Total cumulé : {total_hadiths} hadiths")

        # Checkpoint toutes les 500 entrées
        if hadiths_since_checkpoint >= CHECKPOINT_EVERY:
            print(f"  [CHECKPOINT] Sauvegarde intermédiaire ({hadiths_since_checkpoint} depuis dernier checkpoint)...")
            save_dump(all_data)
            save_checkpoint({"done_editions": list(done_editions), "total_hadiths": total_hadiths})
            hadiths_since_checkpoint = 0

    # Sauvegarde finale
    print(f"\n[FINAL] Sauvegarde finale...")
    save_dump(all_data)
    save_checkpoint({"done_editions": list(done_editions), "total_hadiths": total_hadiths})

    print(f"\n{'='*50}")
    print(f"TERMINÉ — {len(done_editions)}/{len(FR_EDITIONS)} éditions téléchargées")
    print(f"TOTAL HADITHS FR : {total_hadiths}")
    print(f"Fichier : {OUTPUT_FILE}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
