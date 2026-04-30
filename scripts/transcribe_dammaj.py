#!/usr/bin/env python3
"""
Transcription des cours audio Omdatu al-Ahkam (Dammāj) avec OpenAI Whisper
Explication des hadiths du livre de la Salat — Prioritaire pour Al-Mīzān

Usage:
    python transcribe_dammaj.py --model medium
    python transcribe_dammaj.py --model large --segment-hadiths

Modèles disponibles:
    - tiny (39M) : rapide, tests
    - base (74M) : équilibre vitesse/précision  
    - small (244M) : RECOMMANDÉ pour hadiths techniques
    - medium (769M) : haute précision — RECOMMANDÉ
    - large (1550M) : précision max — si GPU

Sortie:
    - corpus/raw_books/dammaj_omdatu_al_ahkam/transcriptions/
    - Fichiers .txt par hadith/chapitre
    - JSON structuré avec timestamps
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import warnings

# Configuration des chapitres Omdatu al-Ahkam (Dammāj)
# Basé sur la structure du livre de la Salat
CHAPTERS_CONFIG = {
    "01_introduction": {
        "title": "Introduction — Importance de la Salat",
        "hadith_range": "1-10",
        "zones_related": ["04", "02", "30"],
        "topics": ["importance_salat", "abandon_salat", "kufr"]
    },
    "02_les_temps": {
        "title": "Les temps de la prière — Début et fin",
        "hadith_range": "11-25",
        "zones_related": ["04", "30"],
        "topics": ["awqat_salat", "waqt_dohr", "waqt_asr", "waqt_maghrib", "waqt_ichae", "waqt_fajr"]
    },
    "03_adhan": {
        "title": "L'Adhān et l'Iqāma",
        "hadith_range": "26-40",
        "zones_related": ["04", "31"],
        "topics": ["adhan", "iqama", "muezzin", "conditions_adhan"]
    },
    "04_conditions": {
        "title": "Conditions de la Salat",
        "hadith_range": "41-55",
        "zones_related": ["04", "33"],
        "topics": ["shurut_salat", "tahara", "wudu", "istiqbal_qibla"]
    },
    "05_les_piliers": {
        "title": "Les piliers (Arkān) de la Salat",
        "hadith_range": "56-75",
        "zones_related": ["04", "33"],
        "topics": ["arkan_salat", "ruku", "sujud", "qiyam", "qira"]
    },
    "06_les_obligations": {
        "title": "Les obligations (Wājibāt)",
        "hadith_range": "76-90",
        "zones_related": ["04"],
        "topics": ["wajibat_salat", "tashahhud", "taslim", "takbir"]
    },
    "07_les_sunnas": {
        "title": "Les Sunnas de la Salat",
        "hadith_range": "91-110",
        "zones_related": ["04"],
        "topics": ["sunnas_salat", "qunut", "dua", "adhkar"]
    },
    "08_annulant": {
        "title": "Ce qui annule la Salat",
        "hadith_range": "111-125",
        "zones_related": ["04", "08"],
        "topics": ["mubtilat_salat", "hadath", "najasa", "qiyam_ramadan"]
    },
    "09_femmes": {
        "title": "La Salat des femmes et particularités",
        "hadith_range": "126-140",
        "zones_related": ["04", "30"],
        "topics": ["salat_femmes", "hayd", "nifas", "tarjih"]
    },
    "10_conclusion": {
        "title": "Conclusion et révisions",
        "hadith_range": "141-150",
        "zones_related": ["04", "16"],
        "topics": ["recapitulatif", "ahkam_ikhtilaf"]
    },
}

# Chemins
BASE_DIR = Path(__file__).parent.parent  # Remonter à la racine du projet
AUDIO_DIR = BASE_DIR / "corpus" / "raw_books" / "dammaj_omdatu_al_ahkam"
OUTPUT_DIR = AUDIO_DIR / "transcriptions"


def find_audio_files() -> List[Path]:
    """Trouve les fichiers MP3/MAA du cours Dammāj."""
    if not AUDIO_DIR.exists():
        print(f"[ERREUR] Dossier audio introuvable: {AUDIO_DIR}")
        print("[INFO] Créez le dossier et placez les MP3 de Dammāj")
        return []
    
    files = sorted(AUDIO_DIR.glob("*.mp3")) + sorted(AUDIO_DIR.glob("*.m4a"))
    return files


def transcribe_with_whisper(
    audio_path: Path,
    model: str = "small",
    language: str = "fr"
) -> Optional[Dict]:
    """
    Transcrit un fichier audio avec OpenAI Whisper.
    Retourne le texte transcrit et les segments.
    """
    try:
        import whisper
        
        print(f"[WHISPER] Chargement modèle '{model}'...")
        model_whisper = whisper.load_model(model)
        
        print(f"[WHISPER] Transcription: {audio_path.name}")
        result = model_whisper.transcribe(
            str(audio_path),
            language=language,
            verbose=False,
            fp16=False  # CPU
        )
        
        return {
            "text": result["text"],
            "segments": result.get("segments", []),
            "language": result.get("language", language)
        }
        
    except ImportError:
        print("[ERREUR] Whisper non installé. Installez: pip install openai-whisper")
        return None
    except Exception as e:
        print(f"[ERREUR] Transcription échouée: {e}")
        return None


def save_transcription(
    chapter_id: str,
    transcription: Dict,
    config: Dict
) -> Path:
    """Sauvegarde la transcription dans un fichier texte et JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fichier texte brut
    txt_path = OUTPUT_DIR / f"{chapter_id}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {config['title']}\n")
        f.write(f"# Hadiths: {config['hadith_range']}\n")
        f.write(f"# Zones: {', '.join(map(str, config['zones_related']))}\n")
        f.write(f"# Topics: {', '.join(config['topics'])}\n")
        f.write("=" * 60 + "\n\n")
        f.write(transcription["text"])
    
    # Fichier JSON structuré
    json_path = OUTPUT_DIR / f"{chapter_id}.json"
    json_data = {
        "chapter_id": chapter_id,
        "title": config["title"],
        "hadith_range": config["hadith_range"],
        "zones_related": config["zones_related"],
        "topics": config["topics"],
        "language": transcription["language"],
        "text": transcription["text"],
        "segments": transcription["segments"],
        "segment_count": len(transcription["segments"])
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    return txt_path


def main():
    parser = argparse.ArgumentParser(
        description="Transcription des cours Dammāj (Omdatu al-Ahkam)"
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Modèle Whisper (small recommandé, medium haute qualité)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister les chapitres configurés"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\n[CHAPITRES CONFIGURÉS — Omdatu al-Ahkam (Dammāj)]")
        print("=" * 60)
        for ch_id, cfg in CHAPTERS_CONFIG.items():
            print(f"\n{ch_id}:")
            print(f"  Titre: {cfg['title']}")
            print(f"  Hadiths: {cfg['hadith_range']}")
            print(f"  Zones: {cfg['zones_related']}")
        return
    
    # Vérifier FFmpeg
    import shutil
    if not shutil.which("ffmpeg"):
        print("[ERREUR] FFmpeg non trouvé dans le PATH")
        print("[INFO] Installez FFmpeg: https://ffmpeg.org/download.html")
        return
    
    # Trouver les fichiers audio
    audio_files = find_audio_files()
    if not audio_files:
        print("[ERREUR] Aucun fichier MP3/M4A trouvé")
        print(f"[INFO] Placez les fichiers audio dans: {AUDIO_DIR}")
        return
    
    print(f"\n[TRANScription DAMMĀJ — {len(audio_files)} fichiers]")
    print(f"[MODÈLE] Whisper: {args.model}")
    print("=" * 60)
    
    # Transcrire chaque fichier
    results = []
    for audio_path in audio_files:
        chapter_id = audio_path.stem
        config = CHAPTERS_CONFIG.get(chapter_id, {
            "title": chapter_id,
            "hadith_range": "?",
            "zones_related": ["04"],
            "topics": ["general"]
        })
        
        print(f"\n[{chapter_id}] {config['title']}")
        
        transcription = transcribe_with_whisper(audio_path, args.model)
        if transcription:
            txt_path = save_transcription(chapter_id, transcription, config)
            print(f"  ✓ Sauvegardé: {txt_path}")
            results.append({
                "chapter": chapter_id,
                "status": "success",
                "segments": len(transcription["segments"])
            })
        else:
            results.append({
                "chapter": chapter_id,
                "status": "failed"
            })
    
    # Rapport final
    print("\n" + "=" * 60)
    print("[RÉSUMÉ]")
    success = sum(1 for r in results if r["status"] == "success")
    print(f"  Succès: {success}/{len(results)}")
    print(f"  Sortie: {OUTPUT_DIR}")
    
    # Sauvegarder rapport
    report_path = OUTPUT_DIR / "transcription_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": str(Path().stat().st_mtime),
            "model": args.model,
            "total_files": len(results),
            "successful": success,
            "failed": len(results) - success,
            "chapters": results
        }, f, indent=2)
    print(f"  Rapport: {report_path}")


if __name__ == "__main__":
    main()
