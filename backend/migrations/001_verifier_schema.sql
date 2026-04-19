-- ═══════════════════════════════════════════════════════════
-- AL-MĪZĀN v5.0 — VÉRIFICATEUR DE HADITH (32 ZONES)
-- Migration : Extension du schéma pour le système de vérification
-- Méthodologie : Salafi (Naqil) — transmission des verdicts des imams
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- EXTENSION TABLE hadiths (colonnes manquantes)
-- ═══════════════════════════════════════════════════════════
ALTER TABLE hadiths ADD COLUMN matn_ar_normalized TEXT;
ALTER TABLE hadiths ADD COLUMN isnad_ar TEXT;
ALTER TABLE hadiths ADD COLUMN sahabi_rawi TEXT;         -- Sahabi qui rapporte
ALTER TABLE hadiths ADD COLUMN type_rafa TEXT;           -- marfuʿ/mawquf/maqtuʿ/qudsi
ALTER TABLE hadiths ADD COLUMN type_tawatur TEXT;        -- mutawatir/mashhur/ʿaziz/gharib
ALTER TABLE hadiths ADD COLUMN grade_synthese TEXT;      -- sahih/hasan/daif/mawduʿ (jugement consolidé)
ALTER TABLE hadiths ADD COLUMN grade_confidence REAL;    -- 0.0-1.0
ALTER TABLE hadiths ADD COLUMN verified_at DATETIME;

CREATE INDEX IF NOT EXISTS idx_hadiths_grade ON hadiths(grade_synthese);
CREATE INDEX IF NOT EXISTS idx_hadiths_sahabi ON hadiths(sahabi_rawi);

-- ═══════════════════════════════════════════════════════════
-- RECHERCHE FULL-TEXT (normalisation arabe)
-- ═══════════════════════════════════════════════════════════
CREATE VIRTUAL TABLE IF NOT EXISTS hadiths_fts USING fts5(
  matn_ar_normalized, matn_ar, matn_fr,
  content='hadiths', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);

-- ═══════════════════════════════════════════════════════════
-- ZONES 13-16 : BASE RIJĀL (narrateurs)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS rijal (
  id INTEGER PRIMARY KEY,
  full_name_ar TEXT NOT NULL,
  kunyah TEXT,
  nasab TEXT,
  laqab TEXT,
  birth_hijri INTEGER,
  death_hijri INTEGER,
  tabaqah INTEGER,              -- 12 niveaux d'Ibn Ḥajar
  residence TEXT,
  taqrib_grade TEXT,            -- thiqah/saduq/maqbul/daif/matruk/kadhdhab
  summary_ar TEXT,
  summary_fr TEXT,
  source_refs TEXT,             -- JSON : Tahdhīb, Taqrīb, Mīzān al-Iʿtidāl...
  UNIQUE(full_name_ar, birth_hijri, death_hijri)
);

CREATE TABLE IF NOT EXISTS rijal_verdicts (
  id INTEGER PRIMARY KEY,
  rawi_id INTEGER REFERENCES rijal(id) ON DELETE CASCADE,
  critic_name TEXT NOT NULL,    -- Yaḥyā ibn Maʿīn, Aḥmad, Bukhārī, Dāraquṭnī...
  verdict_ar TEXT,
  verdict_level INTEGER,        -- -6 (kadhdhab) à +6 (thiqah thabt imam)
  source_book TEXT,
  source_page TEXT
);

CREATE TABLE IF NOT EXISTS rijal_relations (
  id INTEGER PRIMARY KEY,
  master_id INTEGER REFERENCES rijal(id),
  student_id INTEGER REFERENCES rijal(id),
  liqaa_confirmed BOOLEAN DEFAULT 0,
  muʿasarah_possible BOOLEAN DEFAULT 0,
  source TEXT,
  UNIQUE(master_id, student_id)
);

-- ═══════════════════════════════════════════════════════════
-- ZONES 6-12 : CHAÎNES DE TRANSMISSION (sanad)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS sanad_chains (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_order INTEGER DEFAULT 1,
  is_primary BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sanad_links (
  id INTEGER PRIMARY KEY,
  chain_id INTEGER REFERENCES sanad_chains(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,     -- 1 = proche du Prophète, N = compilateur
  rawi_id INTEGER REFERENCES rijal(id),
  rawi_name_raw TEXT,            -- texte brut si pas encore rattaché à rijal
  sigha_ada TEXT,                -- haddathana/akhbarana/ʿan/anna/samiʿtu
  tadlis_flag BOOLEAN DEFAULT 0,
  inqitaʿ_flag BOOLEAN DEFAULT 0,
  ikhtilat_flag BOOLEAN DEFAULT 0,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_sanad_hadith ON sanad_chains(hadith_id);

-- ═══════════════════════════════════════════════════════════
-- ZONES 28-30 : VERDICTS (AHKĀM) — le cœur du vérificateur
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS hukm_sources (
  id INTEGER PRIMARY KEY,
  name_ar TEXT NOT NULL,
  name_fr TEXT,
  era TEXT,                      -- classical / contemporary
  manhaj TEXT,                   -- salafi / etc.
  reliability_weight REAL DEFAULT 1.0,
  UNIQUE(name_ar)
);

-- Pré-remplir les principales références
INSERT OR IGNORE INTO hukm_sources (name_ar, name_fr, era, manhaj) VALUES
  ('البخاري', 'al-Bukhārī', 'classical', 'ahl_al_hadith'),
  ('مسلم', 'Muslim', 'classical', 'ahl_al_hadith'),
  ('الترمذي', 'al-Tirmidhī', 'classical', 'ahl_al_hadith'),
  ('الدارقطني', 'al-Dāraqutnī', 'classical', 'ahl_al_hadith'),
  ('ابن حجر', 'Ibn Ḥajar al-ʿAsqalānī', 'classical', 'ahl_al_hadith'),
  ('النووي', 'al-Nawawī', 'classical', 'ahl_al_hadith'),
  ('ابن القيم', 'Ibn al-Qayyim', 'classical', 'salafi'),
  ('الذهبي', 'al-Dhahabī', 'classical', 'ahl_al_hadith'),
  ('الألباني', 'al-Albānī', 'contemporary', 'salafi'),
  ('ابن باز', 'Ibn Bāz', 'contemporary', 'salafi'),
  ('ابن عثيمين', 'Ibn ʿUthaymīn', 'contemporary', 'salafi'),
  ('مقبل الوادعي', 'Muqbil al-Wādiʿī', 'contemporary', 'salafi'),
  ('شعيب الأرناؤوط', 'Shuʿayb al-Arnaʾūṭ', 'contemporary', 'ahl_al_hadith');

CREATE TABLE IF NOT EXISTS ahkam (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  source_id INTEGER REFERENCES hukm_sources(id),
  hukm_class TEXT NOT NULL,      -- sahih_li_dhatihi / sahih_li_ghayrihi / hasan_li_dhatihi / hasan_li_ghayrihi / daif / mawduʿ / munkar / shadhdh
  hukm_raw_ar TEXT,              -- formulation originale
  source_book TEXT,              -- Ṣaḥīḥa / Ḍaʿīfa / Fatḥ al-Bārī...
  source_volume TEXT,
  source_page TEXT,
  scraped_from TEXT,             -- URL dorar.net / hadeethenc / etc.
  scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ahkam_hadith ON ahkam(hadith_id);
CREATE INDEX IF NOT EXISTS idx_ahkam_class ON ahkam(hukm_class);

-- ═══════════════════════════════════════════════════════════
-- ZONES 1-5 : TAKHRĪJ (cross-références)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS takhrij (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  linked_hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL,   -- same / mutabaʿah / shahid / riwayah_variant
  similarity_score REAL,
  detection_method TEXT,         -- hash / fts_match / embedding / manual
  UNIQUE(hadith_id, linked_hadith_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_takhrij_hadith ON takhrij(hadith_id);

-- ═══════════════════════════════════════════════════════════
-- ZONES 19-23 : ʿILAL (défauts)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ilal (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  ilal_type TEXT NOT NULL,       -- mursal/munqatiʿ/muʿdal/muʿallaq/idtirab/shudhudh/nakarah/idraj/qalb/tashif
  visibility TEXT,               -- zahirah / khafiyyah
  detected_by TEXT,              -- nom du savant qui l'a détecté
  description_ar TEXT,
  description_fr TEXT,
  source_ref TEXT
);

-- ═══════════════════════════════════════════════════════════
-- ZONES 24-27 : ANALYSE DU MATN
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS matn_analysis (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  quran_concordance TEXT,        -- JSON [{sura:2,ayah:255,note:"..."}]
  sunnah_concordance TEXT,       -- JSON [hadith_ids]
  sunnah_opposition TEXT,        -- JSON [hadith_ids]
  linguistic_flags TEXT,         -- JSON {rakaka: false, prophetic_style: true, ...}
  alteration_flags TEXT,         -- JSON {idraj: false, qalb: false, ...}
  analysis_source TEXT           -- savant / LLM-assisté
);

-- ═══════════════════════════════════════════════════════════
-- ZONES 31-32 : CONTEXTE ET FIQH
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS fiqh_hadith (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  asbab_wurud_ar TEXT,
  asbab_wurud_fr TEXT,
  is_nasikh BOOLEAN DEFAULT 0,
  is_mansukh BOOLEAN DEFAULT 0,
  abrogates_hadith_id INTEGER,
  abrogated_by_hadith_id INTEGER,
  gharib_alfath TEXT,            -- JSON {"kalimah": "explication"}
  fiqh_implications_fr TEXT,
  source_refs TEXT
);