# EXTRACTION COMPLÈTE DES BASES DE DONNÉES

**Date**: 2026-04-19T15:26:00+02:00

## BASE: MIZAN

### Statistiques

- **Total hadiths**: 122927
- **Collections**: 10
- **Tables**: 30

### Tables présentes

- `ahkam`
- `avis_savants`
- `errors_log`
- `fiqh_hadith`
- `hadiths`
- `hadiths_fts`
- `hadiths_fts_config`
- `hadiths_fts_data`
- `hadiths_fts_docsize`
- `hadiths_fts_idx`
- `hukm_classes`
- `hukm_sources`
- `ilal`
- `lexique_fer`
- `matn_analysis`
- `mazid_muttasil`
- `mubham_muhmal`
- `mukhtalif_hadith`
- `rijal`
- `rijal_relations`
- `rijal_verdicts`
- `sanad_chains`
- `sanad_links`
- `sqlite_sequence`
- `tafarrud`
- `takhrij`
- `taʿarud_waqf_rafʿ`
- `taʿarud_wasl_irsal`
- `ziyadat_thiqah`
- `ʿamal_salaf`

### Grades distincts (7)

- ``
- `daif`
- `hasan`
- `mawdu`
- `non_évalué`
- `sahih`
- `unknown`

### Répartition par grade

- ****: 72446 hadiths
- **sahih**: 23564 hadiths
- **non_évalué**: 20557 hadiths
- **daif**: 4204 hadiths
- **hasan**: 1692 hadiths
- **unknown**: 411 hadiths
- **mawdu**: 53 hadiths

### Collections présentes

- **Sunan an-Nasa'i**: 27693 hadiths
- **Sahih al-Bukhari**: 21493 hadiths
- **Sahih Muslim**: 19580 hadiths
- **Sunan Abu Dawud**: 15812 hadiths
- **Jami at-Tirmidhi**: 11144 hadiths
- **Sunan Ibn Majah**: 8676 hadiths
- **Musnad Ahmad**: 8600 hadiths
- **Muwatta Malik**: 6987 hadiths
- **Sunan ad-Darimi**: 2900 hadiths
- **forty_hadith_nawawi**: 42 hadiths

### Exemples de hadiths

#### Hadith 1

- **ID**: 1
- **Collection**: Sahih al-Bukhari
- **Numéro**: 1
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ ، قَالَ : حَدَّثَنَا سُفْيَانُ ، قَالَ : ح...

#### Hadith 2

- **ID**: 2
- **Collection**: Sahih al-Bukhari
- **Numéro**: 2
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ، قَالَ أَخْبَرَنَا مَالِكٌ، عَنْ هِشَامِ بْنِ عُرْوَةَ، عَنْ ...

#### Hadith 3

- **ID**: 3
- **Collection**: Sahih al-Bukhari
- **Numéro**: 3
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ، قَالَ حَدَّثَنَا اللَّيْثُ، عَنْ عُقَيْلٍ، عَنِ ابْنِ شِهَابٍ، عَن...

### Schéma complet

```sql
CREATE TABLE ahkam (
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

CREATE TABLE avis_savants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_sha256   TEXT NOT NULL REFERENCES hadiths(sha256),
    savant          TEXT NOT NULL,                 -- voir WHITELIST
    epoque          TEXT NOT NULL,                 -- MUTAQADDIMUN | KHALAF | MUASIR
    jugement        TEXT NOT NULL,                 -- texte du hukm
    source_jugement TEXT
);

CREATE TABLE errors_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    error_type  TEXT NOT NULL,  -- TAAWIL_DETECTED | API_ERROR | INSERT_ERROR
    sha256      TEXT,
    details     TEXT,
    collection  TEXT
);

CREATE TABLE fiqh_hadith (
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

CREATE TABLE hadiths (
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
, matn_ar_normalized TEXT, isnad_ar TEXT, sahabi_rawi TEXT, type_rafa TEXT, type_tawatur TEXT, grade_synthese TEXT, grade_confidence REAL, verified_at DATETIME);

CREATE VIRTUAL TABLE hadiths_fts USING fts5(
  matn_ar_normalized, matn_ar, matn_fr,
  content='hadiths', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE 'hadiths_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;

CREATE TABLE 'hadiths_fts_data'(id INTEGER PRIMARY KEY, block BLOB);

CREATE TABLE 'hadiths_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);

CREATE TABLE 'hadiths_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;

CREATE TABLE hukm_classes (
  code TEXT PRIMARY KEY,
  name_ar TEXT NOT NULL,
  name_fr TEXT NOT NULL,
  category TEXT NOT NULL,        -- maqbul / mardud / typologie / meta
  sub_category TEXT,             -- accepté_fort / accepté_faible / rejeté_sanad / rejeté_rawi / altération / typologie
  severity INTEGER,              -- échelle 0-10 (0=mawdūʿ, 10=sahih mutawātir)
  can_be_acted_upon BOOLEAN,     -- peut-on l'utiliser pour ʿamal
  acted_upon_scope TEXT,         -- ahkam / fadail / aucun
  description_ar TEXT,
  description_fr TEXT
);

CREATE TABLE hukm_sources (
  id INTEGER PRIMARY KEY,
  name_ar TEXT NOT NULL,
  name_fr TEXT,
  era TEXT,
  manhaj TEXT,
  reliability_weight REAL DEFAULT 1.0, tabaqah TEXT, death_hijri INTEGER, specialty TEXT,
  UNIQUE(name_ar)
);

CREATE TABLE ilal (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  ilal_type TEXT NOT NULL,
  visibility TEXT,
  detected_by TEXT,
  description_ar TEXT,
  description_fr TEXT,
  source_ref TEXT
);

CREATE TABLE lexique_fer (
    terme_ar TEXT PRIMARY KEY,
    terme_fr TEXT NOT NULL,
    interdit TEXT NOT NULL  -- la traduction interdite (ta'wil)
);

CREATE TABLE matn_analysis (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  quran_concordance TEXT,
  sunnah_concordance TEXT,
  sunnah_opposition TEXT,
  linguistic_flags TEXT,
  alteration_flags TEXT,
  analysis_source TEXT
);

CREATE TABLE mazid_muttasil (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_id INTEGER REFERENCES sanad_chains(id),
  added_rawi_id INTEGER REFERENCES rijal(id),
  added_rawi_name TEXT,
  position INTEGER,              -- position du maillon ajouté
  who_added_it TEXT,             -- qui a ajouté ce maillon
  verdict TEXT CHECK(verdict IN (
    'sahih_addition',            -- ajout correct
    'khata_mardud',              -- erreur rejetée
    'tawaqquf'                   -- suspension du jugement
  )),
  detected_by TEXT,              -- imam qui l'a détecté
  detected_source TEXT,
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mubham_muhmal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_id INTEGER REFERENCES sanad_chains(id),
  position_in_chain INTEGER,
  is_mubham BOOLEAN DEFAULT 0,   -- non nommé (ex: "رجل")
  is_muhmal BOOLEAN DEFAULT 0,   -- ambigu (ex: "محمد" sans précision)
  mubham_expression TEXT,        -- ex: "حدثني رجل"
  muhmal_name TEXT,              -- ex: "محمد"
  candidates TEXT,               -- JSON [rawi_id potentiels]
  candidates_names TEXT,         -- JSON [noms lisibles]
  resolved_rawi_id INTEGER REFERENCES rijal(id),
  resolved_rawi_name TEXT,
  resolution_source TEXT,        -- ex: "Ibn Ḥajar, Taʿjīl al-Manfaʿah, p.125"
  resolution_confidence TEXT CHECK(resolution_confidence IN (
    'certain',                   -- identification certaine
    'probable',                  -- probable
    'possible',                  -- possible
    'unresolved'                 -- non résolu
  )),
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mukhtalif_hadith (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  conflicting_hadith_id INTEGER REFERENCES hadiths(id),
  conflicting_hadith_text TEXT,
  conflicting_quran_ref TEXT,    -- sūra:āya si conflit avec Qurʾān
  conflicting_quran_text TEXT,
  conflict_type TEXT CHECK(conflict_type IN (
    'hadith_vs_hadith',
    'hadith_vs_quran',
    'hadith_vs_ijmaʿ'
  )),
  resolution_method TEXT CHECK(resolution_method IN (
    'jamʿ',                      -- réconciliation
    'naskh',                     -- abrogation
    'tarjīḥ',                    -- préférence
    'tawaqquf'                   -- suspension
  )),
  resolution_ar TEXT,
  resolution_fr TEXT,
  source_imam TEXT,              -- qui a proposé cette réconciliation
  source_reference TEXT,
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rijal (
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

CREATE TABLE rijal_relations (
  id INTEGER PRIMARY KEY,
  master_id INTEGER REFERENCES rijal(id),
  student_id INTEGER REFERENCES rijal(id),
  liqaa_confirmed BOOLEAN DEFAULT 0,
  muʿasarah_possible BOOLEAN DEFAULT 0,
  source TEXT,
  UNIQUE(master_id, student_id)
);

CREATE TABLE rijal_verdicts (
  id INTEGER PRIMARY KEY,
  rawi_id INTEGER REFERENCES rijal(id) ON DELETE CASCADE,
  critic_name TEXT NOT NULL,
  verdict_ar TEXT,
  verdict_level INTEGER,
  source_book TEXT,
  source_page TEXT
);

CREATE TABLE sanad_chains (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_order INTEGER DEFAULT 1,
  is_primary BOOLEAN DEFAULT 1
);

CREATE TABLE sanad_links (
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

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE tafarrud (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  is_tafarrud BOOLEAN DEFAULT 0,
  unique_narrator_id INTEGER REFERENCES rijal(id),
  unique_narrator_name TEXT,
  position_of_uniqueness INTEGER,  -- à quel niveau de la chaîne
  is_ghareeb_mutlaq BOOLEAN DEFAULT 0,  -- unique dès la source
  is_ghareeb_nisbi BOOLEAN DEFAULT 0,   -- unique par un certain maillon
  acceptable BOOLEAN,                    -- selon l'école mutaqaddimīn
  acceptable_reason TEXT,
  reasoning_source TEXT,
  mutaqaddimin_verdict TEXT,             -- verdict des anciens
  mutaakhkhirin_verdict TEXT,            -- verdict des tardifs
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE takhrij (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  linked_hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL,
  similarity_score REAL,
  detection_method TEXT,
  UNIQUE(hadith_id, linked_hadith_id, relation_type)
);

CREATE TABLE taʿarud_waqf_rafʿ (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  rafʿ_chains TEXT,              -- JSON [chain_ids marfūʿ]
  waqf_chains TEXT,              -- JSON [chain_ids mawqūf]
  rafʿ_narrators TEXT,           -- JSON [noms]
  waqf_narrators TEXT,           -- JSON [noms]
  imam_trajih TEXT,
  imam_trajih_source TEXT,
  final_verdict TEXT CHECK(final_verdict IN (
    'al_mahfuz_al_rafʿ',      -- élévation préservée
    'al_mahfuz_al_waqf',       -- arrêt préservé
    'lahu_hukm_al_rafʿ',      -- a le statut d'élevé
    'muʿallal'                 -- défaut caché
  )),
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE taʿarud_wasl_irsal (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  wasl_chains TEXT,              -- JSON [chain_ids connectés]
  irsal_chains TEXT,             -- JSON [chain_ids mursal]
  wasl_narrators TEXT,           -- JSON [noms des rāwī qui ont connecté]
  irsal_narrators TEXT,          -- JSON [noms des rāwī qui ont fait irsāl]
  imam_trajih TEXT,              -- qui a privilégié quelle version
  imam_trajih_source TEXT,
  final_verdict TEXT CHECK(final_verdict IN (
    'wasl_akbar',              -- connexion plus forte
    'irsal_akbar',             -- irsāl plus fort
    'mahfuz_wasl',             -- version connectée préservée
    'mahfuz_irsal',            -- version mursal préservée
    'muʿallal'                 -- défaut caché
  )),
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ziyadat_thiqah (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  ziyadah_text_ar TEXT NOT NULL,
  ziyadah_text_fr TEXT,
  location TEXT CHECK(location IN ('sanad', 'matn', 'both')),
  ziyadah_type TEXT CHECK(ziyadah_type IN (
    'wasl_mursal',           -- connexion d'un mursal
    'rafʿ_mawquf',          -- élévation d'un mawqūf
    'ziyādat_lafẓ',         -- ajout de mots dans le matn
    'ziyādat_rāwī'          -- ajout d'un maillon dans le sanad
  )),
  narrator_who_added_id INTEGER REFERENCES rijal(id),
  narrator_who_added_name TEXT,
  contradicts_more_reliable BOOLEAN DEFAULT 0,
  verdict TEXT CHECK(verdict IN ('accepted', 'rejected', 'tawaqquf')),
  verdict_source TEXT,
  verdict_source_page TEXT,
  qara_in TEXT,                -- JSON : indices contextuels
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ʿamal_salaf (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  sahabah_who_acted TEXT,        -- JSON [noms des compagnons]
  tabiʿin_who_acted TEXT,        -- JSON [noms des successeurs]
  ijmaʿ_sahaba BOOLEAN DEFAULT 0,
  athar_sources TEXT,            -- JSON [références aux athārs]
  fuqaha_references TEXT,        -- JSON [mentions dans ouvrages fiqh]
  practice_description_ar TEXT,
  practice_description_fr TEXT,
  strengthens_hadith BOOLEAN DEFAULT 0,  -- renforce le hadith ?
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

```

## BASE: ALMIZANE

### Statistiques

- **Total hadiths**: 122927
- **Collections**: 13
- **Tables**: 29

### Tables présentes

- `ahkam`
- `avis_savants`
- `errors_log`
- `fiqh_hadith`
- `hadiths`
- `hadiths_fts`
- `hadiths_fts_config`
- `hadiths_fts_data`
- `hadiths_fts_docsize`
- `hadiths_fts_idx`
- `hukm_sources`
- `ilal`
- `lexique_fer`
- `matn_analysis`
- `mazid_muttasil`
- `mubham_muhmal`
- `mukhtalif_hadith`
- `rijal`
- `rijal_relations`
- `rijal_verdicts`
- `sanad_chains`
- `sanad_links`
- `sqlite_sequence`
- `tafarrud`
- `takhrij`
- `taʿarud_waqf_rafʿ`
- `taʿarud_wasl_irsal`
- `ziyadat_thiqah`
- `ʿamal_salaf`

### Grades distincts (7)

- ``
- `daif`
- `hasan`
- `mawdu`
- `non_évalué`
- `sahih`
- `unknown`

### Répartition par grade

- ****: 72446 hadiths
- **sahih**: 23564 hadiths
- **non_évalué**: 20557 hadiths
- **daif**: 4204 hadiths
- **hasan**: 1692 hadiths
- **unknown**: 411 hadiths
- **mawdu**: 53 hadiths

### Collections présentes

- **Sunan an-Nasa'i**: 27693 hadiths
- **Sahih al-Bukhari**: 21493 hadiths
- **Sahih Muslim**: 19580 hadiths
- **Sunan Abu Dawud**: 10544 hadiths
- **Musnad Ahmad**: 8600 hadiths
- **Jami at-Tirmidhi**: 7519 hadiths
- **Muwatta Malik**: 6987 hadiths
- **abudawud**: 5268 hadiths
- **Sunan Ibn Majah**: 4338 hadiths
- **ibnmajah**: 4338 hadiths
- **tirmidzi**: 3625 hadiths
- **Sunan ad-Darimi**: 2900 hadiths
- **40 Hadith Nawawi**: 42 hadiths

### Exemples de hadiths

#### Hadith 1

- **ID**: 1
- **Collection**: Sahih al-Bukhari
- **Numéro**: 1
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا الْحُمَيْدِيُّ عَبْدُ اللَّهِ بْنُ الزُّبَيْرِ ، قَالَ : حَدَّثَنَا سُفْيَانُ ، قَالَ : ح...

#### Hadith 2

- **ID**: 2
- **Collection**: Sahih al-Bukhari
- **Numéro**: 2
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا عَبْدُ اللَّهِ بْنُ يُوسُفَ، قَالَ أَخْبَرَنَا مَالِكٌ، عَنْ هِشَامِ بْنِ عُرْوَةَ، عَنْ ...

#### Hadith 3

- **ID**: 3
- **Collection**: Sahih al-Bukhari
- **Numéro**: 3
- **Grade**: 
- **Source API**: jsdelivr_cdn
- **Matn (extrait)**: حَدَّثَنَا يَحْيَى بْنُ بُكَيْرٍ، قَالَ حَدَّثَنَا اللَّيْثُ، عَنْ عُقَيْلٍ، عَنِ ابْنِ شِهَابٍ، عَن...

### Schéma complet

```sql
CREATE TABLE ahkam (
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

CREATE TABLE avis_savants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_sha256   TEXT NOT NULL REFERENCES hadiths(sha256),
    savant          TEXT NOT NULL,                 -- voir WHITELIST
    epoque          TEXT NOT NULL,                 -- MUTAQADDIMUN | KHALAF | MUASIR
    jugement        TEXT NOT NULL,                 -- texte du hukm
    source_jugement TEXT
);

CREATE TABLE errors_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    error_type  TEXT NOT NULL,  -- TAAWIL_DETECTED | API_ERROR | INSERT_ERROR
    sha256      TEXT,
    details     TEXT,
    collection  TEXT
);

CREATE TABLE fiqh_hadith (
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

CREATE TABLE hadiths (
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
, matn_ar_normalized TEXT, isnad_ar TEXT, sahabi_rawi TEXT, type_rafa TEXT, type_tawatur TEXT, grade_synthese TEXT, grade_confidence REAL, verified_at DATETIME);

CREATE VIRTUAL TABLE hadiths_fts USING fts5(
  matn_ar_normalized, matn_ar, matn_fr,
  content='hadiths', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE 'hadiths_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;

CREATE TABLE 'hadiths_fts_data'(id INTEGER PRIMARY KEY, block BLOB);

CREATE TABLE 'hadiths_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);

CREATE TABLE 'hadiths_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;

CREATE TABLE hukm_sources (
  id INTEGER PRIMARY KEY,
  name_ar TEXT NOT NULL,
  name_fr TEXT,
  era TEXT,
  manhaj TEXT,
  reliability_weight REAL DEFAULT 1.0, tabaqah TEXT, death_hijri INTEGER, specialty TEXT,
  UNIQUE(name_ar)
);

CREATE TABLE ilal (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  ilal_type TEXT NOT NULL,
  visibility TEXT,
  detected_by TEXT,
  description_ar TEXT,
  description_fr TEXT,
  source_ref TEXT
);

CREATE TABLE lexique_fer (
    terme_ar TEXT PRIMARY KEY,
    terme_fr TEXT NOT NULL,
    interdit TEXT NOT NULL  -- la traduction interdite (ta'wil)
);

CREATE TABLE matn_analysis (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  quran_concordance TEXT,
  sunnah_concordance TEXT,
  sunnah_opposition TEXT,
  linguistic_flags TEXT,
  alteration_flags TEXT,
  analysis_source TEXT
);

CREATE TABLE mazid_muttasil (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_id INTEGER REFERENCES sanad_chains(id),
  added_rawi_id INTEGER REFERENCES rijal(id),
  added_rawi_name TEXT,
  position INTEGER,              -- position du maillon ajouté
  who_added_it TEXT,             -- qui a ajouté ce maillon
  verdict TEXT CHECK(verdict IN (
    'sahih_addition',            -- ajout correct
    'khata_mardud',              -- erreur rejetée
    'tawaqquf'                   -- suspension du jugement
  )),
  detected_by TEXT,              -- imam qui l'a détecté
  detected_source TEXT,
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mubham_muhmal (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_id INTEGER REFERENCES sanad_chains(id),
  position_in_chain INTEGER,
  is_mubham BOOLEAN DEFAULT 0,   -- non nommé (ex: "رجل")
  is_muhmal BOOLEAN DEFAULT 0,   -- ambigu (ex: "محمد" sans précision)
  mubham_expression TEXT,        -- ex: "حدثني رجل"
  muhmal_name TEXT,              -- ex: "محمد"
  candidates TEXT,               -- JSON [rawi_id potentiels]
  candidates_names TEXT,         -- JSON [noms lisibles]
  resolved_rawi_id INTEGER REFERENCES rijal(id),
  resolved_rawi_name TEXT,
  resolution_source TEXT,        -- ex: "Ibn Ḥajar, Taʿjīl al-Manfaʿah, p.125"
  resolution_confidence TEXT CHECK(resolution_confidence IN (
    'certain',                   -- identification certaine
    'probable',                  -- probable
    'possible',                  -- possible
    'unresolved'                 -- non résolu
  )),
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mukhtalif_hadith (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  conflicting_hadith_id INTEGER REFERENCES hadiths(id),
  conflicting_hadith_text TEXT,
  conflicting_quran_ref TEXT,    -- sūra:āya si conflit avec Qurʾān
  conflicting_quran_text TEXT,
  conflict_type TEXT CHECK(conflict_type IN (
    'hadith_vs_hadith',
    'hadith_vs_quran',
    'hadith_vs_ijmaʿ'
  )),
  resolution_method TEXT CHECK(resolution_method IN (
    'jamʿ',                      -- réconciliation
    'naskh',                     -- abrogation
    'tarjīḥ',                    -- préférence
    'tawaqquf'                   -- suspension
  )),
  resolution_ar TEXT,
  resolution_fr TEXT,
  source_imam TEXT,              -- qui a proposé cette réconciliation
  source_reference TEXT,
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rijal (
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

CREATE TABLE rijal_relations (
  id INTEGER PRIMARY KEY,
  master_id INTEGER REFERENCES rijal(id),
  student_id INTEGER REFERENCES rijal(id),
  liqaa_confirmed BOOLEAN DEFAULT 0,
  muʿasarah_possible BOOLEAN DEFAULT 0,
  source TEXT,
  UNIQUE(master_id, student_id)
);

CREATE TABLE rijal_verdicts (
  id INTEGER PRIMARY KEY,
  rawi_id INTEGER REFERENCES rijal(id) ON DELETE CASCADE,
  critic_name TEXT NOT NULL,
  verdict_ar TEXT,
  verdict_level INTEGER,
  source_book TEXT,
  source_page TEXT
);

CREATE TABLE sanad_chains (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  chain_order INTEGER DEFAULT 1,
  is_primary BOOLEAN DEFAULT 1
);

CREATE TABLE sanad_links (
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

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE tafarrud (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  is_tafarrud BOOLEAN DEFAULT 0,
  unique_narrator_id INTEGER REFERENCES rijal(id),
  unique_narrator_name TEXT,
  position_of_uniqueness INTEGER,  -- à quel niveau de la chaîne
  is_ghareeb_mutlaq BOOLEAN DEFAULT 0,  -- unique dès la source
  is_ghareeb_nisbi BOOLEAN DEFAULT 0,   -- unique par un certain maillon
  acceptable BOOLEAN,                    -- selon l'école mutaqaddimīn
  acceptable_reason TEXT,
  reasoning_source TEXT,
  mutaqaddimin_verdict TEXT,             -- verdict des anciens
  mutaakhkhirin_verdict TEXT,            -- verdict des tardifs
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE takhrij (
  id INTEGER PRIMARY KEY,
  hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  linked_hadith_id INTEGER REFERENCES hadiths(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL,
  similarity_score REAL,
  detection_method TEXT,
  UNIQUE(hadith_id, linked_hadith_id, relation_type)
);

CREATE TABLE taʿarud_waqf_rafʿ (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  rafʿ_chains TEXT,              -- JSON [chain_ids marfūʿ]
  waqf_chains TEXT,              -- JSON [chain_ids mawqūf]
  rafʿ_narrators TEXT,           -- JSON [noms]
  waqf_narrators TEXT,           -- JSON [noms]
  imam_trajih TEXT,
  imam_trajih_source TEXT,
  final_verdict TEXT CHECK(final_verdict IN (
    'al_mahfuz_al_rafʿ',      -- élévation préservée
    'al_mahfuz_al_waqf',       -- arrêt préservé
    'lahu_hukm_al_rafʿ',      -- a le statut d'élevé
    'muʿallal'                 -- défaut caché
  )),
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE taʿarud_wasl_irsal (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  wasl_chains TEXT,              -- JSON [chain_ids connectés]
  irsal_chains TEXT,             -- JSON [chain_ids mursal]
  wasl_narrators TEXT,           -- JSON [noms des rāwī qui ont connecté]
  irsal_narrators TEXT,          -- JSON [noms des rāwī qui ont fait irsāl]
  imam_trajih TEXT,              -- qui a privilégié quelle version
  imam_trajih_source TEXT,
  final_verdict TEXT CHECK(final_verdict IN (
    'wasl_akbar',              -- connexion plus forte
    'irsal_akbar',             -- irsāl plus fort
    'mahfuz_wasl',             -- version connectée préservée
    'mahfuz_irsal',            -- version mursal préservée
    'muʿallal'                 -- défaut caché
  )),
  reasoning_ar TEXT,
  reasoning_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ziyadat_thiqah (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  hadith_id INTEGER NOT NULL REFERENCES hadiths(id) ON DELETE CASCADE,
  ziyadah_text_ar TEXT NOT NULL,
  ziyadah_text_fr TEXT,
  location TEXT CHECK(location IN ('sanad', 'matn', 'both')),
  ziyadah_type TEXT CHECK(ziyadah_type IN (
    'wasl_mursal',           -- connexion d'un mursal
    'rafʿ_mawquf',          -- élévation d'un mawqūf
    'ziyādat_lafẓ',         -- ajout de mots dans le matn
    'ziyādat_rāwī'          -- ajout d'un maillon dans le sanad
  )),
  narrator_who_added_id INTEGER REFERENCES rijal(id),
  narrator_who_added_name TEXT,
  contradicts_more_reliable BOOLEAN DEFAULT 0,
  verdict TEXT CHECK(verdict IN ('accepted', 'rejected', 'tawaqquf')),
  verdict_source TEXT,
  verdict_source_page TEXT,
  qara_in TEXT,                -- JSON : indices contextuels
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ʿamal_salaf (
  hadith_id INTEGER PRIMARY KEY REFERENCES hadiths(id) ON DELETE CASCADE,
  sahabah_who_acted TEXT,        -- JSON [noms des compagnons]
  tabiʿin_who_acted TEXT,        -- JSON [noms des successeurs]
  ijmaʿ_sahaba BOOLEAN DEFAULT 0,
  athar_sources TEXT,            -- JSON [références aux athārs]
  fuqaha_references TEXT,        -- JSON [mentions dans ouvrages fiqh]
  practice_description_ar TEXT,
  practice_description_fr TEXT,
  strengthens_hadith BOOLEAN DEFAULT 0,  -- renforce le hadith ?
  notes_ar TEXT,
  notes_fr TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

```

