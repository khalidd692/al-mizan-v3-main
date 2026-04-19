-- ═══════════════════════════════════════════════════════════
-- MIGRATION VÉRIFICATEUR 32 ZONES pour almizane.db
-- Base existante : hadiths avec colonnes (id, sha256, collection, 
-- numero_hadith, livre, chapitre, matn_ar, matn_fr, isnad_brut, 
-- grade_final, categorie, badge_alerte, source_url, source_api, inserted_at)
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- EXTENSION TABLE hadiths (nouvelles colonnes)
-- ═══════════════════════════════════════════════════════════
ALTER TABLE hadiths ADD COLUMN matn_ar_normalized TEXT;
ALTER TABLE hadiths ADD COLUMN isnad_ar TEXT;
ALTER TABLE hadiths ADD COLUMN sahabi_rawi TEXT;
ALTER TABLE hadiths ADD COLUMN type_rafa TEXT;
ALTER TABLE hadiths ADD COLUMN type_tawatur TEXT;
ALTER TABLE hadiths ADD COLUMN grade_synthese TEXT;
ALTER TABLE hadiths ADD COLUMN grade_confidence REAL;
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
  tabaqah INTEGER,
  residence TEXT,
  taqrib_grade TEXT,
  summary_ar TEXT,
  summary_fr TEXT,
  source_refs TEXT,
  UNIQUE(full_name_ar, birth_hijri, death_hijri)
);

CREATE TABLE IF NOT EXISTS rijal_verdicts (
  id INTEGER PRIMARY KEY,
  rawi_id INTEGER REFERENCES rijal(id) ON DELETE CASCADE,
  critic_name TEXT NOT NULL,
  verdict_ar TEXT,
  verdict_level INTEGER,
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
  position INTEGER NOT NULL,
  rawi_id INTEGER REFERENCES rijal(id),
  rawi_name_raw TEXT,
  sigha_ada TEXT,
  tadlis_flag BOOLEAN DEFAULT 0,
  inqitaʿ_flag BOOLEAN DEFAULT 0,
  ikhtilat_flag BOOLEAN DEFAULT 0,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_sanad_hadith ON sanad_chains(hadith_id);

-- ═══════════════════════════════════════════════════════════
-- ZONES 28-30 : VERDICTS (AHKĀM)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS hukm_sources (
  id INTEGER PRIMARY KEY,
  name_ar TEXT NOT NULL,
  name_fr TEXT,
  era TEXT,
  manhaj TEXT,
  reliability_weight REAL DEFAULT 1.0,
  UNIQUE(name_ar)
);

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
  hukm_class TEXT NOT NULL,
  hukm_raw_ar TEXT,
  source_book TEXT,
  source_volume TEXT,
  source_page TEXT,
  scraped_from TEXT,
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
  relation_type TEXT NOT NULL,
  similarity_score REAL,
  detection_method TEXT,
  UNIQUE(hadith_id, linked_hadith_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_takhrij_hadith ON takhrij(hadith_id);

-- ═══════════════════════════════════════════════════════════
-- ZONES 19-23 : ʿILAL (défauts)
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ilal (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  ilal_type TEXT NOT NULL,
  visibility TEXT,
  detected_by TEXT,
  description_ar TEXT,
  description_fr TEXT,
  source_ref TEXT
);

-- ═══════════════════════════════════════════════════════════
-- ZONES 24-27 : ANALYSE DU MATN
-- ═══════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS matn_analysis (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  quran_concordance TEXT,
  sunnah_concordance TEXT,
  sunnah_opposition TEXT,
  linguistic_flags TEXT,
  alteration_flags TEXT,
  analysis_source TEXT
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
  gharib_alfath TEXT,
  fiqh_implications_fr TEXT,
  source_refs TEXT
);