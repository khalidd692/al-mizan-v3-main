-- ============================================================================
-- MIGRATION 002 : ZONES 33-40 (EXTENSION v2 DU VÉRIFICATEUR MÎZÂN)
-- ============================================================================
-- Conforme au BRIEF_CLINE_v2_EXTENSION_32_ZONES-1.md
-- Basé sur la méthodologie des mutaqaddimūn, mutaʾakhkhirūn et muʿāṣirūn
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 33 : ZIYĀDAT AL-THIQAH (زيادة الثقة)
-- ────────────────────────────────────────────────────────────────────────────
-- Quand un rāwī fiable ajoute un mot, une phrase, ou un maillon
-- que les autres n'ont pas rapporté.
-- Référence : Ibn al-Ṣalāḥ (fann laṭīf), al-Albānī (Silsilas)

CREATE TABLE IF NOT EXISTS ziyadat_thiqah (
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

CREATE INDEX IF NOT EXISTS idx_ziyadat_hadith ON ziyadat_thiqah(hadith_id);
CREATE INDEX IF NOT EXISTS idx_ziyadat_narrator ON ziyadat_thiqah(narrator_who_added_id);
CREATE INDEX IF NOT EXISTS idx_ziyadat_verdict ON ziyadat_thiqah(verdict);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 34 : TAʿĀRUḌ AL-WAṢL WA AL-IRSĀL (تعارض الوصل والإرسال)
-- ────────────────────────────────────────────────────────────────────────────
-- Divergence : certaines chaînes connectées (muttaṣil), d'autres mursal
-- Référence : al-Dāraquṭnī (ʿIlal), al-Tirmidhī (Kitāb al-ʿIlal al-Kabīr)

CREATE TABLE IF NOT EXISTS taʿarud_wasl_irsal (
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

CREATE INDEX IF NOT EXISTS idx_taʿarud_wasl_verdict ON taʿarud_wasl_irsal(final_verdict);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 35 : TAʿĀRUḌ AL-WAQF WA AL-RAFʿ (تعارض الوقف والرفع)
-- ────────────────────────────────────────────────────────────────────────────
-- Certaines chaînes marfūʿ (au Prophète ﷺ), d'autres mawqūf (au compagnon)
-- Référence : al-Dāraquṭnī, Abū Ḥātim, Ibn al-Madīnī

CREATE TABLE IF NOT EXISTS taʿarud_waqf_rafʿ (
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

CREATE INDEX IF NOT EXISTS idx_taʿarud_rafʿ_verdict ON taʿarud_waqf_rafʿ(final_verdict);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 36 : AL-MUBHAM WA AL-MUHMAL (المبهم والمهمل)
-- ────────────────────────────────────────────────────────────────────────────
-- Narrateur non nommé (mubham) ou nommé de manière ambiguë (muhmal)
-- Référence : al-Khaṭīb (al-Asmāʾ al-Mubhamah), Ibn Ḥajar (Nuzhat al-Albāb)

CREATE TABLE IF NOT EXISTS mubham_muhmal (
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

CREATE INDEX IF NOT EXISTS idx_mubham_hadith ON mubham_muhmal(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mubham_chain ON mubham_muhmal(chain_id);
CREATE INDEX IF NOT EXISTS idx_mubham_resolved ON mubham_muhmal(resolved_rawi_id);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 37 : AL-MAZĪD FĪ MUTTAṢIL AL-ASĀNĪD (المزيد في متصل الأسانيد)
-- ────────────────────────────────────────────────────────────────────────────
-- Un rāwī ajoute un maillon intermédiaire dans une chaîne
-- Référence : al-Khaṭīb al-Baghdādī (al-Mazīd fī Muttaṣil al-Asānīd)

CREATE TABLE IF NOT EXISTS mazid_muttasil (
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

CREATE INDEX IF NOT EXISTS idx_mazid_hadith ON mazid_muttasil(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mazid_chain ON mazid_muttasil(chain_id);
CREATE INDEX IF NOT EXISTS idx_mazid_verdict ON mazid_muttasil(verdict);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 38 : TAFARRUD (التفرد)
-- ────────────────────────────────────────────────────────────────────────────
-- Quand un rāwī fiable est SEUL à rapporter un hadith
-- Référence : Yaḥyā ibn Saʿīd al-Qaṭṭān, ʿAlī ibn al-Madīnī, Ḥamzah al-Malībārī

CREATE TABLE IF NOT EXISTS tafarrud (
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

CREATE INDEX IF NOT EXISTS idx_tafarrud_narrator ON tafarrud(unique_narrator_id);
CREATE INDEX IF NOT EXISTS idx_tafarrud_acceptable ON tafarrud(acceptable);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 39 : ʿAMAL AL-ṢAḤĀBAH WA AL-TĀBIʿĪN (عمل الصحابة والتابعين)
-- ────────────────────────────────────────────────────────────────────────────
-- Les compagnons et successeurs ont-ils agi selon ce hadith ?
-- Référence : Ibn Taymiyyah, Ibn al-Qayyim (pilier du manhaj salafi)

CREATE TABLE IF NOT EXISTS ʿamal_salaf (
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

CREATE INDEX IF NOT EXISTS idx_ʿamal_ijmaʿ ON ʿamal_salaf(ijmaʿ_sahaba);
CREATE INDEX IF NOT EXISTS idx_ʿamal_strengthens ON ʿamal_salaf(strengthens_hadith);

-- ────────────────────────────────────────────────────────────────────────────
-- ZONE 40 : MUKHTALIF AL-ḤADĪTH WA MUSHKILUH (مختلف الحديث ومشكله)
-- ────────────────────────────────────────────────────────────────────────────
-- Hadiths qui semblent contredire d'autres hadiths authentiques ou le Qurʾān
-- Référence : Ibn Qutaybah, al-Ṭaḥāwī, Ibn al-Jawzī

CREATE TABLE IF NOT EXISTS mukhtalif_hadith (
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

CREATE INDEX IF NOT EXISTS idx_mukhtalif_hadith ON mukhtalif_hadith(hadith_id);
CREATE INDEX IF NOT EXISTS idx_mukhtalif_conflicting ON mukhtalif_hadith(conflicting_hadith_id);
CREATE INDEX IF NOT EXISTS idx_mukhtalif_method ON mukhtalif_hadith(resolution_method);

-- ────────────────────────────────────────────────────────────────────────────
-- TRIGGERS POUR updated_at
-- ────────────────────────────────────────────────────────────────────────────

CREATE TRIGGER IF NOT EXISTS update_ziyadat_timestamp 
AFTER UPDATE ON ziyadat_thiqah
BEGIN
  UPDATE ziyadat_thiqah SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_taʿarud_wasl_timestamp 
AFTER UPDATE ON taʿarud_wasl_irsal
BEGIN
  UPDATE taʿarud_wasl_irsal SET updated_at = CURRENT_TIMESTAMP WHERE hadith_id = NEW.hadith_id;
END;

CREATE TRIGGER IF NOT EXISTS update_taʿarud_rafʿ_timestamp 
AFTER UPDATE ON taʿarud_waqf_rafʿ
BEGIN
  UPDATE taʿarud_waqf_rafʿ SET updated_at = CURRENT_TIMESTAMP WHERE hadith_id = NEW.hadith_id;
END;

CREATE TRIGGER IF NOT EXISTS update_mubham_timestamp 
AFTER UPDATE ON mubham_muhmal
BEGIN
  UPDATE mubham_muhmal SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_mazid_timestamp 
AFTER UPDATE ON mazid_muttasil
BEGIN
  UPDATE mazid_muttasil SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tafarrud_timestamp 
AFTER UPDATE ON tafarrud
BEGIN
  UPDATE tafarrud SET updated_at = CURRENT_TIMESTAMP WHERE hadith_id = NEW.hadith_id;
END;

CREATE TRIGGER IF NOT EXISTS update_ʿamal_timestamp 
AFTER UPDATE ON ʿamal_salaf
BEGIN
  UPDATE ʿamal_salaf SET updated_at = CURRENT_TIMESTAMP WHERE hadith_id = NEW.hadith_id;
END;

CREATE TRIGGER IF NOT EXISTS update_mukhtalif_timestamp 
AFTER UPDATE ON mukhtalif_hadith
BEGIN
  UPDATE mukhtalif_hadith SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- FIN DE LA MIGRATION 002
-- ============================================================================