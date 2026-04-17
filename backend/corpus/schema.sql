-- Al-Mīzān v5.0 — Schéma Base de Données SQLite
-- Date: 17 avril 2026
-- Objectif: Stockage hadiths bruts + validés + review manuelle

-- ═══════════════════════════════════════════════════════════════
-- TABLE 1: HADITHS BRUTS (Harvester Dorar.net)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS hadiths_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dorar_id TEXT UNIQUE NOT NULL,           -- ID unique Dorar.net
    matn_ar TEXT NOT NULL,                   -- Texte arabe du hadith
    source TEXT,                             -- Ex: "Ṣaḥīḥ al-Bukhārī n°1"
    grade_raw TEXT,                          -- Grade brut (ex: "صحيح")
    rawi TEXT,                               -- Narrateur principal
    harvested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0              -- 0 = non traité, 1 = traité
);

-- ═══════════════════════════════════════════════════════════════
-- TABLE 2: HADITHS VALIDÉS (Après pipeline 4 agents)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS hadiths_validated (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_raw_id INTEGER NOT NULL REFERENCES hadiths_raw(id),
    matn_ar TEXT NOT NULL,
    translation_fr TEXT,                     -- Traduction Lexique de Fer
    grade_normalized TEXT NOT NULL,          -- صحيح / حسن / ضعيف / موضوع
    scholar_verdict TEXT,                    -- Nom du savant validé
    scholar_location TEXT,                   -- Médine / Arabie Saoudite / TAWAQQUF
    confidence_score REAL NOT NULL,          -- 0-100
    agent_isnad_output TEXT,                 -- JSON output agent Isnād
    agent_ilal_output TEXT,                  -- JSON output agent ʿIlal
    agent_matn_output TEXT,                  -- JSON output agent Matn
    agent_tarjih_output TEXT,                -- JSON output agent Tarjīḥ
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hadith_raw_id)
);

-- ═══════════════════════════════════════════════════════════════
-- TABLE 3: REVIEW MANUELLE (Confiance < 85%)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pending_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_raw_id INTEGER NOT NULL REFERENCES hadiths_raw(id),
    reason TEXT NOT NULL,                    -- Raison du rejet auto
    confidence_score REAL NOT NULL,
    agent_outputs TEXT,                      -- JSON combiné des 4 agents
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT 0,              -- 0 = en attente, 1 = reviewé
    reviewer_notes TEXT
);

-- ═══════════════════════════════════════════════════════════════
-- INDEX POUR PERFORMANCES
-- ═══════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_hadiths_raw_processed 
    ON hadiths_raw(processed);

CREATE INDEX IF NOT EXISTS idx_hadiths_raw_dorar_id 
    ON hadiths_raw(dorar_id);

CREATE INDEX IF NOT EXISTS idx_hadiths_validated_grade 
    ON hadiths_validated(grade_normalized);

CREATE INDEX IF NOT EXISTS idx_hadiths_validated_confidence 
    ON hadiths_validated(confidence_score);

CREATE INDEX IF NOT EXISTS idx_pending_review_confidence 
    ON pending_review(confidence_score);

CREATE INDEX IF NOT EXISTS idx_pending_review_reviewed 
    ON pending_review(reviewed);

-- ═══════════════════════════════════════════════════════════════
-- VUES UTILES
-- ═══════════════════════════════════════════════════════════════

-- Vue: Hadiths non traités
CREATE VIEW IF NOT EXISTS v_hadiths_unprocessed AS
SELECT * FROM hadiths_raw WHERE processed = 0;

-- Vue: Statistiques globales
CREATE VIEW IF NOT EXISTS v_stats AS
SELECT 
    (SELECT COUNT(*) FROM hadiths_raw) as total_harvested,
    (SELECT COUNT(*) FROM hadiths_raw WHERE processed = 1) as total_processed,
    (SELECT COUNT(*) FROM hadiths_validated) as total_validated,
    (SELECT COUNT(*) FROM pending_review WHERE reviewed = 0) as total_pending_review,
    (SELECT AVG(confidence_score) FROM hadiths_validated) as avg_confidence;