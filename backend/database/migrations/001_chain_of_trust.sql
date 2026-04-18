-- ═══════════════════════════════════════════════════════════════
-- AL-MĪZĀN V8.0 — MIGRATION 001 : CHAIN OF TRUST
-- Sanad numérique vérifiable + historique + quarantaine
-- ═══════════════════════════════════════════════════════════════

-- ÉTAPE 1 : Ajout des colonnes de traçabilité à la table entries
ALTER TABLE entries ADD COLUMN content_hash TEXT;
ALTER TABLE entries ADD COLUMN source_fetch_sha TEXT;
ALTER TABLE entries ADD COLUMN merkle_parent TEXT;
ALTER TABLE entries ADD COLUMN lexique_version TEXT;
ALTER TABLE entries ADD COLUMN needs_human_review INTEGER DEFAULT 0;

-- Index unique sur content_hash pour éviter les doublons
CREATE UNIQUE INDEX IF NOT EXISTS idx_entries_content_hash ON entries(content_hash);

-- Index pour les revues humaines
CREATE INDEX IF NOT EXISTS idx_entries_needs_review ON entries(needs_human_review) WHERE needs_human_review = 1;

-- ÉTAPE 2 : Table d'historique pour audit trail complet
CREATE TABLE IF NOT EXISTS entries_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    content_hash TEXT, -- Peut être NULL pour les anciennes entrées
    snapshot_json TEXT NOT NULL, -- Ligne complète sérialisée en JSON
    archived_at TEXT DEFAULT (datetime('now')),
    reason TEXT,
    FOREIGN KEY (entry_id) REFERENCES entries(id)
);

CREATE INDEX IF NOT EXISTS idx_history_entry_id ON entries_history(entry_id);
CREATE INDEX IF NOT EXISTS idx_history_archived_at ON entries_history(archived_at);

-- ÉTAPE 3 : Table de quarantaine pour les entrées problématiques
CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    raw_json TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_detail TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    resolved INTEGER DEFAULT 0,
    resolved_at TEXT,
    resolution_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_quarantine_error_type ON quarantine(error_type);
CREATE INDEX IF NOT EXISTS idx_quarantine_resolved ON quarantine(resolved) WHERE resolved = 0;

-- ÉTAPE 4 : Trigger d'audit AVANT UPDATE sur entries
-- Sauvegarde automatique de l'état précédent dans entries_history
CREATE TRIGGER IF NOT EXISTS trg_entries_audit_before_update
BEFORE UPDATE ON entries
FOR EACH ROW
BEGIN
    INSERT INTO entries_history (entry_id, content_hash, snapshot_json, reason)
    VALUES (
        OLD.id,
        OLD.content_hash,
        json_object(
            'id', OLD.id,
            'ar_text', OLD.ar_text,
            'fr_text', OLD.fr_text,
            'ar_full_isnad', OLD.ar_full_isnad,
            'grade_primary', OLD.grade_primary,
            'grade_by_mohdith', OLD.grade_by_mohdith,
            'book_name_ar', OLD.book_name_ar,
            'book_name_fr', OLD.book_name_fr,
            'zone_id', OLD.zone_id,
            'content_hash', OLD.content_hash,
            'source_fetch_sha', OLD.source_fetch_sha,
            'lexique_version', OLD.lexique_version,
            'needs_human_review', OLD.needs_human_review
        ),
        'auto_snapshot_before_update'
    );
END;

-- ÉTAPE 5 : Vue pour les statistiques de qualité
CREATE VIEW IF NOT EXISTS v_quality_stats AS
SELECT
    COUNT(*) as total_entries,
    SUM(CASE WHEN content_hash IS NOT NULL THEN 1 ELSE 0 END) as with_hash,
    SUM(CASE WHEN needs_human_review = 1 THEN 1 ELSE 0 END) as needs_review,
    SUM(CASE WHEN lexique_version IS NOT NULL THEN 1 ELSE 0 END) as with_lexique,
    COUNT(DISTINCT lexique_version) as lexique_versions_count
FROM entries;

-- ÉTAPE 6 : Vue pour les entrées nécessitant une revue
CREATE VIEW IF NOT EXISTS v_needs_review AS
SELECT
    id,
    ar_text,
    fr_text,
    grade_primary,
    book_name_ar,
    book_name_fr,
    needs_human_review,
    content_hash,
    lexique_version
FROM entries
WHERE needs_human_review = 1
ORDER BY id DESC;

-- ═══════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION 001
-- ═══════════════════════════════════════════════════════════════