-- ═══════════════════════════════════════════════════════════════
-- AL-MĪZĀN V8.0 — MIGRATION 002 : AUTHORITY MASTER LIST
-- Base de Données des Autorités : Du Prophète ﷺ aux savants contemporains
-- ═══════════════════════════════════════════════════════════════

-- Table principale des autorités (muhaddithūn, fuqahā', 'ulamā')
CREATE TABLE IF NOT EXISTS authorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ar TEXT NOT NULL,
    name_transliterated TEXT NOT NULL,
    name_aliases TEXT, -- JSON array des variantes du nom
    birth_year INTEGER, -- Année hijri de naissance
    death_year INTEGER, -- Année hijri de décès (NULL si vivant)
    century INTEGER NOT NULL, -- Siècle hijri principal d'activité
    era TEXT NOT NULL CHECK(era IN ('sahaba', 'tabiun', 'tabi_tabiun', 'mutaqaddimun', 'mutaakhkhirun', 'contemporary')),
    specialty TEXT NOT NULL CHECK(specialty IN ('hadith', 'fiqh', 'tafsir', 'aqidah', 'usul', 'multiple')),
    school TEXT, -- Madhab (hanafi, maliki, shafii, hanbali, zahiri, salafi, etc.)
    reliability_level TEXT CHECK(reliability_level IN ('thiqah', 'saduq', 'daif', 'matruk', 'unknown')),
    is_imam INTEGER DEFAULT 0, -- 1 si imam reconnu
    is_mujtahid INTEGER DEFAULT 0, -- 1 si mujtahid
    is_hafiz INTEGER DEFAULT 0, -- 1 si hafiz du hadith
    is_muhaddith INTEGER DEFAULT 0, -- 1 si spécialiste du hadith
    is_faqih INTEGER DEFAULT 0, -- 1 si juriste
    is_mufassir INTEGER DEFAULT 0, -- 1 si exégète
    major_works TEXT, -- JSON array des œuvres majeures
    teachers TEXT, -- JSON array des maîtres (shuyukh)
    students TEXT, -- JSON array des élèves (talamidh)
    biography_summary TEXT, -- Résumé biographique
    source_references TEXT, -- JSON array des sources biographiques
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Index pour recherches rapides
CREATE INDEX IF NOT EXISTS idx_authorities_era ON authorities(era);
CREATE INDEX IF NOT EXISTS idx_authorities_century ON authorities(century);
CREATE INDEX IF NOT EXISTS idx_authorities_specialty ON authorities(specialty);
CREATE INDEX IF NOT EXISTS idx_authorities_death_year ON authorities(death_year);
CREATE INDEX IF NOT EXISTS idx_authorities_name_ar ON authorities(name_ar);
CREATE INDEX IF NOT EXISTS idx_authorities_reliability ON authorities(reliability_level);

-- Table de liaison entre hadiths et autorités (qui a gradé quoi)
CREATE TABLE IF NOT EXISTS hadith_gradings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL,
    authority_id INTEGER NOT NULL,
    grade TEXT NOT NULL,
    grade_detail TEXT, -- Détail du jugement
    source_reference TEXT, -- Référence exacte (livre, page)
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entry_id) REFERENCES entries(id),
    FOREIGN KEY (authority_id) REFERENCES authorities(id)
);

CREATE INDEX IF NOT EXISTS idx_gradings_entry ON hadith_gradings(entry_id);
CREATE INDEX IF NOT EXISTS idx_gradings_authority ON hadith_gradings(authority_id);
CREATE INDEX IF NOT EXISTS idx_gradings_grade ON hadith_gradings(grade);

-- Vue pour statistiques par autorité
CREATE VIEW IF NOT EXISTS v_authority_stats AS
SELECT
    a.id,
    a.name_ar,
    a.name_transliterated,
    a.era,
    a.specialty,
    COUNT(hg.id) as total_gradings,
    SUM(CASE WHEN hg.grade = 'Sahih' THEN 1 ELSE 0 END) as sahih_count,
    SUM(CASE WHEN hg.grade = 'Hasan' THEN 1 ELSE 0 END) as hasan_count,
    SUM(CASE WHEN hg.grade = 'Daif' THEN 1 ELSE 0 END) as daif_count
FROM authorities a
LEFT JOIN hadith_gradings hg ON a.id = hg.authority_id
GROUP BY a.id;

-- ═══════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION 002
-- ═══════════════════════════════════════════════════════════════