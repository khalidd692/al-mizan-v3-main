#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDIT INITIAL CORPUS AL-MĪZĀN V6.0
Phase 0 : Inventaire complet et génération des rapports
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def scan_directory(path):
    """Scanner récursif d'un répertoire"""
    files = []
    if os.path.exists(path):
        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                size = os.path.getsize(filepath)
                files.append({
                    'path': filepath,
                    'name': filename,
                    'size': size,
                    'ext': os.path.splitext(filename)[1]
                })
    return files

def analyze_corpus():
    """Analyse complète du corpus existant"""
    print("=== AUDIT CORPUS AL-MĪZĀN V6.0 ===")
    print(f"Date: {datetime.now().isoformat()}\n")
    
    # Scanner les répertoires
    corpus_files = scan_directory('corpus')
    backend_files = scan_directory('backend')
    
    # Statistiques
    stats = {
        'corpus_total': len(corpus_files),
        'backend_total': len(backend_files),
        'corpus_by_ext': defaultdict(int),
        'backend_by_ext': defaultdict(int),
        'total_size_corpus': 0,
        'total_size_backend': 0
    }
    
    for f in corpus_files:
        stats['corpus_by_ext'][f['ext']] += 1
        stats['total_size_corpus'] += f['size']
    
    for f in backend_files:
        stats['backend_by_ext'][f['ext']] += 1
        stats['total_size_backend'] += f['size']
    
    # Affichage console
    print(f"📁 Fichiers corpus: {stats['corpus_total']}")
    print(f"📁 Fichiers backend: {stats['backend_total']}")
    print(f"💾 Taille corpus: {stats['total_size_corpus'] / 1024:.2f} KB")
    print(f"💾 Taille backend: {stats['total_size_backend'] / 1024:.2f} KB\n")
    
    print("Extensions corpus:")
    for ext, count in sorted(stats['corpus_by_ext'].items()):
        print(f"  {ext or '(sans ext)'}: {count}")
    
    print("\nExtensions backend:")
    for ext, count in sorted(stats['backend_by_ext'].items()):
        print(f"  {ext or '(sans ext)'}: {count}")
    
    # Créer le répertoire output
    os.makedirs('output', exist_ok=True)
    
    # Générer corpus_audit_full.json
    audit_data = {
        'timestamp': datetime.now().isoformat(),
        'version': 'V6.0',
        'stats': stats,
        'corpus_files': corpus_files[:100],  # Limiter pour la taille
        'backend_files': backend_files[:100]
    }
    
    with open('output/corpus_audit_full.json', 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)
    print("\n✅ Généré: output/corpus_audit_full.json")
    
    # Générer corpus_audit.md
    with open('output/corpus_audit.md', 'w', encoding='utf-8') as f:
        f.write("# AUDIT CORPUS AL-MĪZĀN V6.0\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Statistiques Globales\n\n")
        f.write(f"| Catégorie | Valeur |\n")
        f.write(f"|-----------|--------|\n")
        f.write(f"| Fichiers corpus | {stats['corpus_total']} |\n")
        f.write(f"| Fichiers backend | {stats['backend_total']} |\n")
        f.write(f"| Taille corpus | {stats['total_size_corpus'] / 1024:.2f} KB |\n")
        f.write(f"| Taille backend | {stats['total_size_backend'] / 1024:.2f} KB |\n\n")
        
        f.write("## Extensions Corpus\n\n")
        f.write("| Extension | Nombre |\n")
        f.write("|-----------|--------|\n")
        for ext, count in sorted(stats['corpus_by_ext'].items()):
            f.write(f"| {ext or '(sans ext)'} | {count} |\n")
        
        f.write("\n## Extensions Backend\n\n")
        f.write("| Extension | Nombre |\n")
        f.write("|-----------|--------|\n")
        for ext, count in sorted(stats['backend_by_ext'].items()):
            f.write(f"| {ext or '(sans ext)'} | {count} |\n")
    
    print("✅ Généré: output/corpus_audit.md")
    
    # Générer zone_coverage.csv (32 zones)
    zones = [
        (1, "Isnad"), (2, "Matn"), (3, "Tarjih"), (4, "Takhrij"), 
        (5, "Ilal"), (6, "Shuruh"), (7, "Naskh"), (8, "Mukhtalif"),
        (9, "Qawaid"), (10, "Fawaid"), (11, "Grading"), (12, "Sahih"),
        (13, "Daif"), (14, "Hasan"), (15, "Mutawatir"), (16, "Ahad"),
        (17, "Mawdu"), (18, "Munkar"), (19, "Shadh"), (20, "Maqlub"),
        (21, "Aqidah"), (22, "Fawaid_Extended"), (23, "Tarjih_Doctrinal"),
        (24, "Shuruh_Savants"), (25, "Naskh_Documented"), (26, "Ilal_Advanced"),
        (27, "Takhrij_Complete"), (28, "Mukhtalif_Hadith"), (29, "Qawaid_Fiqh"),
        (30, "Fatawa_Salafiyyah"), (31, "Manaqib_Sirah"), (32, "Glossaire_Termes")
    ]
    
    with open('output/zone_coverage.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['zone_id', 'zone_name', 'entries_count', 'coverage_percent', 'status'])
        for zone_id, zone_name in zones:
            # Pour l'instant, tout est à 0 (audit initial)
            writer.writerow([zone_id, zone_name, 0, 0.0, 'À remplir'])
    
    print("✅ Généré: output/zone_coverage.csv")
    
    # Générer missing_sources.md
    with open('output/missing_sources.md', 'w', encoding='utf-8') as f:
        f.write("# SOURCES MANQUANTES - AL-MĪZĀN V6.0\n\n")
        f.write("## Sources Prioritaires à Intégrer\n\n")
        f.write("### Dépôts GitHub/Hugging Face\n\n")
        f.write("- [ ] https://github.com/AhmedBaset/hadith-json\n")
        f.write("- [ ] https://github.com/mhashim6/Open-Hadith-Data\n")
        f.write("- [ ] https://github.com/fawazahmed0/hadith-api\n")
        f.write("- [ ] https://github.com/ragaeeb/shamela\n")
        f.write("- [ ] https://huggingface.co/datasets/meeAtif/hadith_datasets\n\n")
        f.write("### Sites Officiels Salafi\n\n")
        f.write("- [ ] binbaz.org.sa\n")
        f.write("- [ ] alifta.gov.sa\n")
        f.write("- [ ] rabee.net\n")
        f.write("- [ ] salafipublications.com\n\n")
        f.write("### Tahqiq Prioritaires\n\n")
        f.write("- [ ] Al-Albānī (Silsilah Sahihah/Daifah)\n")
        f.write("- [ ] Cheikh Muqbil\n")
        f.write("- [ ] Cheikh Bin Bāz\n")
        f.write("- [ ] Cheikh Al-Fawzān\n")
    
    print("✅ Généré: output/missing_sources.md")
    
    print("\n" + "="*50)
    print("AUDIT INITIAL TERMINÉ")
    print("="*50)
    print("\nProchaine étape: Téléchargement des sources prioritaires")

if __name__ == '__main__':
    analyze_corpus()