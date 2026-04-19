-- ════════════════════════════════════════════════════════════════════════════
-- AL-MĪZĀN VÉRIFICATEUR v2.0 — SCHÉMA COMPLET
-- Inclut : schéma de base + tables vérificateur + zones 33-40
-- ════════════════════════════════════════════════════════════════════════════

-- ============================================================================
-- PARTIE 1 : TABLES DE BASE (hadiths + avis_savants)
-- ============================================================================

CREATE TABLE IF NOT EXISTS hadiths (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sha256          TEXT NOT NULL UNIQUE,
    collection      TEXT NOT NULL,
    numero_hadith   TEXT,
    livre           TEXT,
    chapitre        TEXT,
    matn_ar         TEXT NOT NULL,
    matn_fr         TEXT,
    isnad_brut      TEXT,
    grade_final     TEXT NOT NULL,
    categorie       TEXT NOT NULL,
    badge_alerte    INTEGER DEFAULT 0,
    source_url      TEXT,
    source_api      TEXT,
    inserted_at     TEXT DEFAULT (datetime('now')),
    -- Colonnes vérificateur
    grade_synthese  TEXT,
    grade_confidence REAL,
    verified_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_hadiths_sha256 ON hadiths(sha256);
CREATE INDEX IF NOT EXISTS idx_hadiths_collection ON hadiths(collection);
CREATE INDEX IF NOT EXISTS idx_hadiths_grade ON hadiths(grade_final);
CREATE INDEX IF NOT EXISTS idx_hadiths_categorie ON hadiths(categorie);

CREATE TABLE IF NOT EXISTS avis_savants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_sha256   TEXT NOT NULL REFERENCES hadiths(sha256),
    savant          TEXT NOT NULL,
    epoque          TEXT NOT NULL,
    jugement        TEXT NOT NULL,
    source_jugement TEXT
);

CREATE INDEX IF NOT EXISTS idx_avis_hadith ON avis_savants(hadith_sha256);
CREATE INDEX IF NOT EXISTS idx_avis_savant ON avis_savants(savant);

-- ============================================================================
-- PARTIE 2 : TABLES VÉRIFICATEUR (zones 1-32)
-- ============================================================================

-- Table des sources de hukm (muḥaddithīn)
CREATE TABLE IF NOT EXISTS hukm_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL UNIQUE,
    name_fr TEXT,
    era TEXT NOT NULL,
    manhaj TEXT NOT NULL,
    reliability_weight REAL DEFAULT 1.0,
    death_hijri INTEGER,
    tabaqah TEXT,
    specialty TEXT
);

-- Table des ahkam (jugements)
CREATE TABLE IF NOT EXISTS ahkam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES hukm_sources(id),
    hukm_class TEXT NOT NULL,
    hukm_text_ar TEXT,
    hukm_text_fr TEXT,
    source_primaire TEXT,
    confidence REAL DEFAULT 0.5,
    UNIQUE(hadith_id, source_id)
);

-- Table des rijāl (narrateurs)
CREATE TABLE IF NOT EXISTS rijal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL,
    name_fr TEXT,
    kunyah TEXT,
    nasab TEXT,
    laqab TEXT,
    birth_year_hijri INTEGER,
    death_year_hijri INTEGER,
    tabaqah INTEGER,
    region TEXT,
    UNIQUE(name_ar, death_year_hijri)
);

-- Table des verdicts sur les rijāl
CREATE TABLE IF NOT EXISTS rijal_verdicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rawi_id INTEGER NOT NULL REFERENCES rijal(id) ON DELETE CASCADE,
    critic_id INTEGER NOT NULL REFERENCES hukm_sources(id),
    verdict_class TEXT NOT NULL,
    verdict_text_ar TEXT,
    source_primaire TEXT,
    UNIQUE(rawi_id, critic_id)
);

-- Table des chaînes de transmission
CREATE TABLE IF NOT EXISTS sanad_chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    chain_text_ar TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 1,
    UNIQUE(hadith_id, chain_text_ar)
);

-- Table des maillons de chaîne
CREATE TABLE IF NOT EXISTS sanad_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL REFERENCES sanad_chains(id) ON DELETE CASCADE,
    rawi_id INTEGER NOT NULL REFERENCES rijal(id),
    position INTEGER NOT NULL,
    sighat_adaa TEXT,
    UNIQUE(chain_id, position)
);

-- Table takhrīj
CREATE TABLE IF NOT EXISTS takhrij (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    collection_name TEXT NOT NULL,
    book_number INTEGER,
    hadith_number TEXT,
    url TEXT,
    is_mutabaa BOOLEAN DEFAULT 0,
    is_shahid BOOLEAN DEFAULT 0
);

-- Table ʿilal (défauts cachés)
CREATE TABLE IF NOT EXISTS ilal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    illah_type TEXT NOT NULL,
    illah_description_ar TEXT,
    detected_by_id INTEGER REFERENCES hukm_sources(id),
    source_primaire TEXT
);

-- Table analyse du matn
CREATE TABLE IF NOT EXISTS matn_analysis (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    has_shudhudh BOOLEAN DEFAULT 0,
    has_munkar BOOLEAN DEFAULT 0,
    has_idraj BOOLEAN DEFAULT 0,
    has_qalb BOOLEAN DEFAULT 0,
    has_idtirab BOOLEAN DEFAULT 0,
    analysis_notes TEXT
);

-- Table fiqh
CREATE TABLE IF NOT EXISTS fiqh_hadith (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    fiqh_topic TEXT,
    ruling_type TEXT,
    asbab_wurud TEXT,
    nasikh_mansukh TEXT,
    ikhtilaf_fuqaha TEXT
);

-- ============================================================================
-- PARTIE 3 : ZONES ADDITIONNELLES 33-40
-- ============================================================================

-- Zone 33 : Ziyādat al-Thiqah
CREATE TABLE IF NOT EXISTS ziyadat_thiqah (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    ziyadah_text_ar TEXT NOT NULL,
    location TEXT,
    ziyadah_type TEXT,
    narrator_who_added_id INTEGER REFERENCES rijal(id),
    contradicts_more_reliable BOOLEAN,
    verdict TEXT,
    verdict_source TEXT,
    qaraa_in TEXT
);

-- Zone 34 : Taʿāruḍ al-Waṣl wa al-Irsāl
CREATE TABLE IF NOT EXISTS taʿarud_wasl_irsal (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    wasl_chains TEXT,
    irsal_chains TEXT,
    imam_trajih TEXT,
    final_verdict TEXT
);

-- Zone 35 : Taʿāruḍ al-Waqf wa al-Rafʿ
CREATE TABLE IF NOT EXISTS taʿarud_waqf_rafʿ (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    rafʿ_chains TEXT,
    waqf_chains TEXT,
    imam_trajih TEXT,
    final_verdict TEXT,
    reasoning_ar TEXT
);

-- Zone 36 : al-Mubham wa al-Muhmal
CREATE TABLE IF NOT EXISTS mubham_muhmal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    chain_id INTEGER REFERENCES sanad_chains(id),
    position_in_chain INTEGER,
    is_mubham BOOLEAN,
    is_muhmal BOOLEAN,
    candidates TEXT,
    resolved_rawi_id INTEGER REFERENCES rijal(id),
    resolution_source TEXT
);

-- Zone 37 : al-Mazīd fī Muttaṣil al-Asānīd
CREATE TABLE IF NOT EXISTS mazid_muttasil (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    chain_id INTEGER REFERENCES sanad_chains(id),
    added_rawi_id INTEGER REFERENCES rijal(id),
    position INTEGER,
    verdict TEXT,
    detected_by TEXT
);

-- Zone 38 : Tafarrud
CREATE TABLE IF NOT EXISTS tafarrud (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    is_tafarrud BOOLEAN,
    unique_narrator_id INTEGER REFERENCES rijal(id),
    position_of_uniqueness INTEGER,
    acceptable BOOLEAN,
    reasoning_source TEXT,
    is_ghareeb_mutlaq BOOLEAN,
    is_ghareeb_nisbi BOOLEAN
);

-- Zone 39 : ʿAmal al-Ṣaḥābah wa al-Tābiʿīn
CREATE TABLE IF NOT EXISTS ʿamal_salaf (
    hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
    sahabah_who_acted TEXT,
    tabiʿin_who_acted TEXT,
    ijmaʿ_sahaba BOOLEAN,
    athar_sources TEXT,
    fuqaha_references TEXT
);

-- Zone 40 : Mukhtalif al-Ḥadīth
CREATE TABLE IF NOT EXISTS mukhtalif_hadith (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
    conflicting_hadith_id INTEGER REFERENCES hadiths(id),
    conflicting_quran_ref TEXT,
    resolution_method TEXT,
    resolution_ar TEXT,
    resolution_fr TEXT,
    source_imam TEXT
);

-- ============================================================================
-- INDEX POUR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ahkam_hadith ON ahkam(hadith_id);
CREATE INDEX IF NOT EXISTS idx_ahkam_source ON ahkam(source_id);
CREATE INDEX IF NOT EXISTS idx_rijal_verdicts_rawi ON rijal_verdicts(rawi_id);
CREATE INDEX IF NOT EXISTS idx_sanad_chains_hadith ON sanad_chains(hadith_id);
CREATE INDEX IF NOT EXISTS idx_sanad_links_chain ON sanad_links(chain_id);
CREATE INDEX IF NOT EXISTS idx_takhrij_hadith ON takhrij(hadith_id);
CREATE INDEX IF NOT EXISTS idx_ilal_hadith ON ilal(hadith_id);
CREATE INDEX IF NOT EXISTS idx_ziyadat_hadith ON ziyadat_thiqah(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mubham_hadith ON mubham_muhmal(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mazid_hadith ON mazid_muttasil(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mukhtalif_hadith ON mukhtalif_hadith(hadith_id);

-- ============================================================================
-- FIN DU SCHÉMA
-- ============================================================================