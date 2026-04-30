#!/usr/bin/env python3
"""
Transcription des cours audio Sharḥ al-Bayqūniyya avec OpenAI Whisper
Segmentation par chapitre pour alimenter les zones 01-09 d'Al-Mīzān

Usage:
    python transcribe_bayquniyya.py --model medium
    python transcribe_bayquniyya.py --model large --segment-chapters

Modèles disponibles:
    - tiny (39M) : rapide, moins précis — pour tests
    - base (74M) : bon équilibre vitesse/précision
    - small (244M) : recommandé pour contenu religieux technique
    - medium (769M) : précision élevée — RECOMMANDÉ pour ce projet
    - large (1550M) : précision maximale — si GPU disponible

Sortie:
    - corpus/raw_books/bayquniyya_uthaymin/transcriptions/
    - Fichiers .txt par chapitre
    - JSON structuré avec timestamps et métadonnées
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import warnings

# Configuration des chapitres selon les 10 fichiers MP3
CHAPTERS_CONFIG = {
    "00_lecture_du_poeme": {
        "title": "Lecture du poème Al-Bayqūniyya",
        "verses": "1-34 (intégral)",
        "zones_related": ["04"],
        "topics": ["introduction", "poème_complet"]
    },
    "01_preface": {
        "title": "Préface — Introduction à la science du Muṣṭalaḥ",
        "verses": "Introduction",
        "zones_related": ["04"],
        "topics": ["définition_mustalah", "importance_terminologie"]
    },
    "02_explication_des_deux_premiers_vers": {
        "title": "Explication des vers 1-2 — Définitions fondamentales",
        "verses": "1-2",
        "zones_related": ["04", "02"],
        "topics": ["marfūʿ", "mawqūf", "maqṭūʿ", "musnad", "muttaṣil"]
    },
    "03_vers_3_a_6": {
        "title": "Explication des vers 3-6 — Ṣaḥīḥ et Ḥasan",
        "verses": "3-6",
        "zones_related": ["04"],
        "topics": ["ṣaḥīḥ_li_dhātihi", "ṣaḥīḥ_li_ghayrihi", "ḥasan_li_dhātihi", "ḥasan_li_ghayrihi"]
    },
    "04_vers_7_a_11": {
        "title": "Explication des vers 7-11 — Āḥād, Mutawātir, classifications",
        "verses": "7-11",
        "zones_related": ["04", "36"],
        "topics": ["al_āḥād", "al_mutawātir", "gharīb", "ʿazīz", "mashhūr"]
    },
    "05_vers_12_a_15": {
        "title": "Explication des vers 12-15 — Ḍaʿīf et ses catégories",
        "verses": "12-15",
        "zones_related": ["04", "08"],
        "topics": ["ḍaʿīf", "causes_faiblesse", "niveaux_daif"]
    },
    "06_vers_16_a_20": {
        "title": "Explication des vers 16-20 — Mursal, Mudallas, Mursal khafī",
        "verses": "16-20",
        "zones_related": ["08", "06"],
        "topics": ["mursal", "mudallas", "tadlīs", "mursal_khafī"]
    },
    "07_vers_21_a_25": {
        "title": "Explication des vers 21-25 — Munkar, Mudraj, classifications avancées",
        "verses": "21-25",
        "zones_related": ["04", "05", "08"],
        "topics": ["munkar", "mudraj", "idrāj", "iltiqāʾ_as_saqāṭayn"]
    },
    "08_vers_26_jusqua_fin_du_poeme": {
        "title": "Explication des vers 26-34 — Maqlūb, Shādhdh, Muʿallal, Muḍṭarib",
        "verses": "26-34",
        "zones_related": ["05", "06", "07"],
        "topics": ["maqlob", "shādhdh", "muʿallal", "ʿillah", "muḍṭarib"]
    },
    "09_revision_concis_du_poeme": {
        "title": "Révision concise du poème — Synthèse complète",
        "verses": "1-34 (révision)",
        "zones_related": ["04", "05", "06", "07", "08"],
        "topics": ["synthèse", "révision_complète"]
    }
}


class BayquniyyaTranscriber:
    """Transcripteur des cours audio Sharḥ al-Bayqūniyya"""
    
    def __init__(self, model: str = "medium", device: str = "cpu", 
                 input_dir: str = "./corpus/raw_books/bayquniyya_uthaymin/",
                 output_dir: str = "./corpus/raw_books/bayquniyya_uthaymin/transcriptions/"):
        self.model = model
        self.device = device
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Vérification de whisper
        self._check_whisper()
    
    def _check_whisper(self):
        """Vérifie que whisper est installé"""
        try:
            import whisper
            self.whisper_module = whisper
            print(f"✅ OpenAI Whisper disponible — modèle: {self.model}")
        except ImportError:
            print("❌ OpenAI Whisper non installé")
            print("   Installation: pip install -U openai-whisper")
            sys.exit(1)
    
    def get_audio_files(self) -> List[Path]:
        """Liste les fichiers MP3 dans l'ordre des chapitres"""
        mp3_files = sorted(self.input_dir.glob("*.mp3"))
        
        # Filtre les fichiers selon la config des chapitres
        ordered_files = []
        for chapter_id in CHAPTERS_CONFIG.keys():
            for mp3 in mp3_files:
                if chapter_id in mp3.stem:
                    ordered_files.append(mp3)
                    break
        
        # Ajoute les fichiers non identifiés à la fin
        for mp3 in mp3_files:
            if mp3 not in ordered_files:
                ordered_files.append(mp3)
        
        return ordered_files
    
    def transcribe_file(self, audio_file: Path) -> Dict:
        """
        Transcrit un fichier audio avec Whisper
        
        Args:
            audio_file: Chemin vers le fichier MP3
            
        Returns:
            Dict avec transcription, segments, métadonnées
        """
        chapter_id = audio_file.stem
        config = CHAPTERS_CONFIG.get(chapter_id, {
            "title": f"Transcription {chapter_id}",
            "verses": "?",
            "zones_related": [],
            "topics": []
        })
        
        print(f"\n{'='*60}")
        print(f"🎙️  {config['title']}")
        print(f"   Fichier: {audio_file.name}")
        print(f"   Vers: {config['verses']}")
        print(f"   Zones: {', '.join(config['zones_related'])}")
        print(f"{'='*60}")
        
        try:
            # Chargement du modèle (lazy — une seule fois serait mieux mais plus complexe)
            print(f"   ⏳ Chargement modèle Whisper ({self.model})...")
            model = self.whisper_module.load_model(self.model)
            
            print(f"   ⏳ Transcription en cours...")
            result = model.transcribe(
                str(audio_file),
                language="fr",  # Les cours sont en français
                task="transcribe",
                verbose=False,
                fp16=(self.device == "cuda")  # FP16 seulement sur GPU
            )
            
            # Structure du résultat
            transcription_data = {
                "chapter_id": chapter_id,
                "title": config["title"],
                "audio_file": str(audio_file.name),
                "verses": config["verses"],
                "zones_related": config["zones_related"],
                "topics": config["topics"],
                "model": self.model,
                "device": self.device,
                "full_text": result["text"],
                "segments": []
            }
            
            # Extraction des segments avec timestamps
            for segment in result.get("segments", []):
                transcription_data["segments"].append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })
            
            print(f"   ✅ Transcription terminée — {len(transcription_data['segments'])} segments")
            return transcription_data
            
        except Exception as e:
            print(f"   ❌ Erreur transcription: {e}")
            return {
                "chapter_id": chapter_id,
                "error": str(e),
                "status": "failed"
            }
    
    def save_transcription(self, data: Dict):
        """Sauvegarde la transcription dans plusieurs formats"""
        chapter_id = data.get("chapter_id", "unknown")
        
        # 1. JSON complet (avec timestamps)
        json_file = self.output_dir / f"{chapter_id}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 2. Texte brut (pour lecture/édition facile)
        txt_file = self.output_dir / f"{chapter_id}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"# {data.get('title', 'Sans titre')}\n")
            f.write(f"# Source: {data.get('audio_file', 'Inconnue')}\n")
            f.write(f"# Modèle: Whisper {data.get('model', 'unknown')}\n")
            f.write(f"# Zones Al-Mīzān: {', '.join(data.get('zones_related', []))}\n")
            f.write(f"# Topics: {', '.join(data.get('topics', []))}\n")
            f.write("="*60 + "\n\n")
            f.write(data.get("full_text", ""))
        
        # 3. Markdown avec segments (pour référence)
        md_file = self.output_dir / f"{chapter_id}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# {data.get('title', 'Sans titre')}\n\n")
            f.write(f"**Source audio:** `{data.get('audio_file', 'Inconnue')}`\n\n")
            f.write(f"**Vers du poème:** {data.get('verses', '?')}\n\n")
            f.write(f"**Zones Al-Mīzān concernées:** {', '.join(data.get('zones_related', []))}\n\n")
            f.write(f"**Topics:** {', '.join(data.get('topics', []))}\n\n")
            f.write(f"**Modèle de transcription:** Whisper {data.get('model', 'unknown')}\n\n")
            f.write("---\n\n")
            
            for seg in data.get("segments", []):
                start = self._format_time(seg["start"])
                end = self._format_time(seg["end"])
                f.write(f"**[{start} → {end}]**\n\n")
                f.write(f"{seg['text']}\n\n")
        
        print(f"   💾 Sauvegardé: {json_file.name}, {txt_file.name}, {md_file.name}")
    
    def _format_time(self, seconds: float) -> str:
        """Formate le temps en MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def run(self, file_filter: Optional[str] = None):
        """
        Lance la transcription de tous les fichiers (ou d'un seul)
        
        Args:
            file_filter: Si spécifié, ne transcrit que ce fichier
        """
        audio_files = self.get_audio_files()
        
        if file_filter:
            audio_files = [f for f in audio_files if file_filter in f.name]
        
        if not audio_files:
            print("❌ Aucun fichier audio trouvé")
            return
        
        print(f"\n🚀 Démarrage transcription — {len(audio_files)} fichier(s)")
        print(f"   Modèle: {self.model} | Device: {self.device}")
        print(f"   Output: {self.output_dir}")
        
        results = []
        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n📁 [{i}/{len(audio_files)}] {audio_file.name}")
            
            # Vérifie si déjà transcrit
            chapter_id = audio_file.stem
            existing_json = self.output_dir / f"{chapter_id}.json"
            
            if existing_json.exists():
                print(f"   ⏭️  Déjà transcrit — {existing_json.name}")
                with open(existing_json, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
                continue
            
            # Transcription
            data = self.transcribe_file(audio_file)
            results.append(data)
            
            if "error" not in data:
                self.save_transcription(data)
            
            # Pause entre les fichiers pour éviter la surcharge thermique
            if i < len(audio_files):
                print("   ⏳ Pause de 2s...")
                import time
                time.sleep(2)
        
        # Rapport final
        self._generate_report(results)
    
    def _generate_report(self, results: List[Dict]):
        """Génère un rapport de transcription"""
        report = {
            "generated_at": self._get_timestamp(),
            "model": self.model,
            "device": self.device,
            "total_files": len(results),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "chapters": []
        }
        
        for r in results:
            chapter_summary = {
                "id": r.get("chapter_id"),
                "title": r.get("title"),
                "status": "error" if "error" in r else "success",
                "zones": r.get("zones_related", [])
            }
            if "error" in r:
                chapter_summary["error"] = r["error"]
            else:
                chapter_summary["segments_count"] = len(r.get("segments", []))
                chapter_summary["text_length"] = len(r.get("full_text", ""))
            
            report["chapters"].append(chapter_summary)
        
        # Sauvegarde le rapport
        report_file = self.output_dir / "transcription_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Affichage
        print(f"\n{'='*60}")
        print("📊 RAPPORT DE TRANSCRIPTION")
        print(f"{'='*60}")
        print(f"Fichiers traités: {report['total_files']}")
        print(f"Succès: {report['successful']} | Échecs: {report['failed']}")
        print()
        
        for ch in report["chapters"]:
            status_icon = "✅" if ch["status"] == "success" else "❌"
            print(f"{status_icon} {ch['id']}")
            if ch["status"] == "success":
                print(f"   → {ch.get('segments_count', 0)} segments, {ch.get('text_length', 0)} caractères")
                print(f"   → Zones: {', '.join(ch['zones'])}")
        
        print(f"\n💾 Rapport complet: {report_file}")
    
    def _get_timestamp(self) -> str:
        """Retourne le timestamp actuel"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    parser = argparse.ArgumentParser(
        description="Transcription des cours audio Sharḥ al-Bayqūniyya avec Whisper"
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="medium",
        help="Modèle Whisper (default: medium)"
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device de calcul (default: cpu)"
    )
    parser.add_argument(
        "--file",
        help="Transcrit uniquement ce fichier spécifique (nom partiel)"
    )
    parser.add_argument(
        "--input-dir",
        default="./corpus/raw_books/bayquniyya_uthaymin/",
        help="Répertoire des fichiers audio"
    )
    parser.add_argument(
        "--output-dir",
        default="./corpus/raw_books/bayquniyya_uthaymin/transcriptions/",
        help="Répertoire de sortie"
    )
    
    args = parser.parse_args()
    
    # Vérification GPU si demandé
    if args.device == "cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                print("⚠️  CUDA non disponible — basculement sur CPU")
                args.device = "cpu"
            else:
                print(f"✅ GPU détecté: {torch.cuda.get_device_name(0)}")
        except ImportError:
            print("⚠️  PyTorch non installé — basculement sur CPU")
            args.device = "cpu"
    
    # Lancement
    transcriber = BayquniyyaTranscriber(
        model=args.model,
        device=args.device,
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    transcriber.run(file_filter=args.file)


if __name__ == "__main__":
    main()
