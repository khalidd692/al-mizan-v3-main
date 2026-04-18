-- ════════════════════════════════════════════════════════════════════════════
-- AL-MĪZĀN v5.0 — SCHÉMA DE BASE DE DONNÉES COMPLET
-- Conforme à Constitution_v4.md (Version 5.0 Unifiée)
-- ════════════════════════════════════════════════════════════════════════════

-- Table principale des hadiths
CREATE TABLE IF NOT EXISTS hadiths (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256          TEXT NOT NULL UNIQUE,          -- Sanad Numérique (hash du matn_ar)
    collection      TEXT NOT NULL,                 -- ex: "Sahih al-Bukhari"
    numero_hadith   TEXT,                          -- numéro dans la collection
    livre           TEXT,
    chapitre        TEXT,
    matn_ar         TEXT NOT NULL,                 -- texte arabe brut
    matn_fr         TEXT,                          -- traduction française
    isnad_brut      TEXT,                          -- chaîne de transmission brute
    grade_final     TEXT NOT NULL,                 -- Sahih, Hasan, Da'if, etc.
    categorie       TEXT NOT NULL,                 -- MAQBUL | DAIF | MAWDUU
    badge_alerte    INTEGER DEFAULT 0,             -- 1 = Mawdū' (rouge obligatoire)
    source_url      TEXT,
    source_api      TEXT,                          -- "dorar_json" | "hadeethenc"
    inserted_at     TEXT DEFAULT (datetime('now'))
);

-- Index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_hadiths_sha256 ON hadiths(sha256);
CREATE INDEX IF NOT EXISTS idx_hadiths_collection ON hadiths(collection);
CREATE INDEX IF NOT EXISTS idx_hadiths_grade ON hadiths(grade_final);
CREATE INDEX IF NOT EXISTS idx_hadiths_categorie ON hadiths(categorie);

-- Table des avis de savants
CREATE TABLE IF NOT EXISTS avis_savants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_sha256   TEXT NOT NULL REFERENCES hadiths(sha256),
    savant          TEXT NOT NULL,                 -- voir WHITELIST
    epoque          TEXT NOT NULL,                 -- MUTAQADDIMUN | KHALAF | MUASIR
    jugement        TEXT NOT NULL,                 -- texte du hukm
    source_jugement TEXT
);

CREATE INDEX IF NOT EXISTS idx_avis_hadith ON avis_savants(hadith_sha256);
CREATE INDEX IF NOT EXISTS idx_avis_savant ON avis_savants(savant);

-- Lexique de Fer (Attributs divins)
CREATE TABLE IF NOT EXISTS lexique_fer (
    terme_ar TEXT PRIMARY KEY,
    terme_fr TEXT NOT NULL,
    interdit TEXT NOT NULL  -- la traduction interdite (ta'wil)
);

-- Insertion du Lexique de Fer
INSERT OR IGNORE INTO lexique_fer VALUES
    ('استوى',  'S''est établi (par Son Essence)',        'S''est installé / a pris le contrôle'),
    ('يد',     'Main (réelle, sans comparaison)',         'Puissance / Grâce'),
    ('نزول',   'Descend (comme Il le mérite)',            'Sa miséricorde descend'),
    ('وجه',    'Visage (réel, sans comparaison)',         'Essence / Être'),
    ('ساق',    'Jambe (réelle, sans comparaison)',        'Sévérité / Épreuve'),
    ('عين',    'Œil/Regard (réel, sans comparaison)',     'Connaissance / Surveillance');

-- Table des erreurs de collecte
CREATE TABLE IF NOT EXISTS errors_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    error_type  TEXT NOT NULL,  -- TAAWIL_DETECTED | API_ERROR | INSERT_ERROR
    sha256      TEXT,
    details     TEXT,
    collection  TEXT
);

CREATE INDEX IF NOT EXISTS idx_errors_type ON errors_log(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors_log(timestamp);