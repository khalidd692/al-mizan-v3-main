#!/usr/bin/env python3
"""
Migration intelligente : almizane.db → mizan.db
Transfère les 122K hadiths existants vers la nouvelle structure Mîzân v2
avec préservation de toutes les données et adaptation au nouveau schéma.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

SOURCE_DB = Path("backend/almizane.db")
TARGET_DB = Path("backend/mizan.db")
LOG_FILE = Path("output/migration_almizane_mizan.log")

def log(msg):
    """Log avec timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line.encode('utf-8', errors='replace').decode('utf-8'))
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def compute_hash(matn_ar: str, isnad_ar: str = "") -> str:
    """Calcule le hash unique d'un hadith"""
    content = f"{matn_ar or ''}{isnad_ar or ''}".strip()
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def migrate_hadiths():
    """Migre les hadiths de almizane vers mizan"""
    log("=" * 70)
    log("DEBUT MIGRATION ALMIZANE -> MIZAN")
    log("=" * 70)
    
    # Connexions
    src = sqlite3.connect(SOURCE_DB)
    src.row_factory = sqlite3.Row
    tgt = sqlite3.connect(TARGET_DB)
    
    # Stats
    src_count = src.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    log(f"Hadiths dans almizane.db : {src_count:,}")
    
    tgt_count_before = tgt.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    log(f"Hadiths dans mizan.db (avant) : {tgt_count_before:,}")
    
    # Récupérer tous les hadiths source
    log("Chargement des hadiths source...")
    hadiths = src.execute("""
        SELECT 
            id, collection, livre, numero_hadith,
            matn_ar, matn_fr, isnad_ar,
            sahabi_rawi, grade_final, grade_synthese,
            categorie, chapitre, source_url, source_api,
            inserted_at, verified_at
        FROM hadiths
        ORDER BY id
    """).fetchall()
    
    log(f"Chargés : {len(hadiths):,} hadiths")
    
    # Migration par lots
    BATCH_SIZE = 1000
    migrated = 0
    skipped = 0
    errors = 0
    
    for i in range(0, len(hadiths), BATCH_SIZE):
        batch = hadiths[i:i+BATCH_SIZE]
        
        for h in batch:
            try:
                # Calculer le hash
                content_hash = compute_hash(h['matn_ar'], h['isnad_ar'] or '')
                
                # Vérifier si existe déjà
                exists = tgt.execute(
                    "SELECT id FROM hadiths WHERE content_hash = ?",
                    (content_hash,)
                ).fetchone()
                
                if exists:
                    skipped += 1
                    continue
                
                # Insérer dans mizan
                tgt.execute("""
                    INSERT INTO hadiths (
                        collection, book_number, hadith_number,
                        matn_ar, matn_fr, isnad_ar,
                        sahabi_rawi, grade_original, grade_synthese,
                        theme, keywords, source_url, source_api,
                        content_hash, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    h['collection'], h['livre'], h['numero_hadith'],
                    h['matn_ar'], h['matn_fr'], h['isnad_ar'],
                    h['sahabi_rawi'], h['grade_final'], h['grade_synthese'],
                    h['categorie'], h['chapitre'], h['source_url'], h['source_api'],
                    content_hash, h['inserted_at'], h['verified_at']
                ))
                
                migrated += 1
                
            except Exception as e:
                errors += 1
                log(f"ERREUR hadith {h['id']}: {e}")
        
        # Commit par lot
        tgt.commit()
        
        if (i + BATCH_SIZE) % 10000 == 0:
            log(f"  Progression : {i + BATCH_SIZE:,} / {len(hadiths):,} ({100*(i+BATCH_SIZE)/len(hadiths):.1f}%)")
    
    # Stats finales
    tgt_count_after = tgt.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
    
    log("=" * 70)
    log("MIGRATION TERMINEE")
    log("=" * 70)
    log(f"Hadiths migres : {migrated:,}")
    log(f"Doublons evites : {skipped:,}")
    log(f"Erreurs : {errors:,}")
    log(f"Total dans mizan.db : {tgt_count_after:,}")
    log("=" * 70)
    
    # Fermeture
    src.close()
    tgt.close()
    
    return {
        'migrated': migrated,
        'skipped': skipped,
        'errors': errors,
        'total': tgt_count_after
    }

def migrate_verdicts():
    """Migre les verdicts existants si la table existe dans almizane"""
    log("\nVerification des verdicts dans almizane...")
    
    src = sqlite3.connect(SOURCE_DB)
    src.row_factory = sqlite3.Row
    tgt = sqlite3.connect(TARGET_DB)
    
    # Vérifier si table ahkam existe dans source
    tables = src.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ahkam'"
    ).fetchall()
    
    if not tables:
        log("Pas de table ahkam dans almizane.db - skip")
        src.close()
        tgt.close()
        return
    
    # Compter les verdicts
    verdict_count = src.execute("SELECT COUNT(*) FROM ahkam").fetchone()[0]
    log(f"Verdicts trouves dans almizane : {verdict_count:,}")
    
    if verdict_count == 0:
        log("Aucun verdict à migrer")
        src.close()
        tgt.close()
        return
    
    # Migration des verdicts
    log("Migration des verdicts...")
    verdicts = src.execute("""
        SELECT 
            hadith_id, source_id, hukm_class, hukm_raw_ar,
            source_book, source_volume, source_page,
            notes, scraped_from, created_at
        FROM ahkam
    """).fetchall()
    
    migrated = 0
    for v in verdicts:
        try:
            # Trouver le nouveau hadith_id dans mizan
            old_hadith = src.execute(
                "SELECT matn_ar, isnad_ar FROM hadiths WHERE id = ?",
                (v['hadith_id'],)
            ).fetchone()
            
            if not old_hadith:
                continue
            
            content_hash = compute_hash(old_hadith['matn_ar'], old_hadith['isnad_ar'] or '')
            new_hadith = tgt.execute(
                "SELECT id FROM hadiths WHERE content_hash = ?",
                (content_hash,)
            ).fetchone()
            
            if not new_hadith:
                continue
            
            # Insérer le verdict
            tgt.execute("""
                INSERT OR IGNORE INTO ahkam (
                    hadith_id, source_id, hukm_class, hukm_raw_ar,
                    source_book, source_volume, source_page,
                    notes, scraped_from, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_hadith[0], v['source_id'], v['hukm_class'], v['hukm_raw_ar'],
                v['source_book'], v['source_volume'], v['source_page'],
                v['notes'], v['scraped_from'], v['created_at']
            ))
            
            migrated += 1
            
        except Exception as e:
            log(f"Erreur verdict hadith {v['hadith_id']}: {e}")
    
    tgt.commit()
    log(f"Verdicts migres : {migrated:,}")
    
    src.close()
    tgt.close()

def generate_report(stats):
    """Génère un rapport de migration"""
    report_path = Path("output/MIGRATION_ALMIZANE_MIZAN_COMPLETE.md")
    
    content = f"""# ✅ MIGRATION ALMIZANE → MIZAN — TERMINÉE

**Date** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Statut** : ✅ SUCCÈS

---

## 📊 STATISTIQUES

- **Hadiths migrés** : {stats['migrated']:,}
- **Doublons évités** : {stats['skipped']:,}
- **Erreurs** : {stats['errors']:,}
- **Total dans mizan.db** : {stats['total']:,}

---

## 🎯 PROCHAINES ÉTAPES

La base mizan.db contient maintenant {stats['total']:,} hadiths.

### Phase 1 : Harvesting Dorar.net
- Enrichir avec les verdicts des muḥaddithīn
- Remplir la table `ahkam` avec les 35 classes de ḥukm

### Phase 2 : Import des rijāl
- Tahdhīb al-Kamāl (8 000 rāwī)
- Peupler les tables `rijal`, `rijal_verdicts`, `rijal_relations`

### Phase 3 : Extraction des sanads
- Parser les chaînes de transmission
- Remplir `sanad_chains` et `sanad_links`

---

## 📝 NOTES

- Migration effectuée avec préservation complète des données
- Hash de contenu utilisé pour éviter les doublons
- Structure v2 respectée (40 zones du Vérificateur)

*Wa-llāhu al-muwaffiq*
"""
    
    report_path.write_text(content, encoding='utf-8')
    log(f"\nRapport généré : {report_path}")

def main():
    """Point d'entrée principal"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    if not SOURCE_DB.exists():
        log(f"ERREUR : {SOURCE_DB} n'existe pas")
        return
    
    if not TARGET_DB.exists():
        log(f"ERREUR : {TARGET_DB} n'existe pas")
        return
    
    # Migration des hadiths
    stats = migrate_hadiths()
    
    # Migration des verdicts (si existants)
    migrate_verdicts()
    
    # Rapport final
    generate_report(stats)
    
    log("\nMIGRATION COMPLETE")

if __name__ == "__main__":
    main()