-- ============================================================
-- AL-MĪZĀN V7.0 — Schéma SQLite complet
-- Généré pour migration depuis V6.0
-- Date: 2026-04-17
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================
-- TABLE PRINCIPALE : entries (hadiths, fatwas, commentaires)
-- ============================================================
CREATE TABLE IF NOT EXISTS entries (
  id                    TEXT PRIMARY KEY,     -- ex: "bukhari-7288" ou UUID
  zone_id               INTEGER NOT NULL,     -- 1-32 (voir mapping zones)
  zone_label            TEXT NOT NULL,        -- label humain de la zone
  
  -- Texte source arabe
  ar_text               TEXT NOT NULL,        -- texte arabe avec tashkîl
  ar_text_clean         TEXT,                 -- texte arabe sans tashkîl (pour recherche)
  ar_narrator           TEXT,                 -- الراوي
  ar_full_isnad         TEXT,                 -- chaîne d'isnad complète si disponible
  
  -- Traduction française
  fr_text               TEXT,                 -- traduction complète en français
  fr_explanation        TEXT,                 -- explication simplifiée (HadeethEnc si dispo)
  fr_source             TEXT CHECK(fr_source IN ('fawazahmed0','hadeethenc','manual','none')),
  fr_summary            TEXT,                 -- résumé court (≤ 280 caractères)
  
  -- Grading (multi-savants)
  grade_primary         TEXT CHECK(grade_primary IN ('Sahih','Hasan','Da''if','Mawdu''','Munkar','Shadh','unknown')),
  grade_by_mohdith      TEXT,                 -- nom du savant gradeur principal
  grade_by_mohdith_id   INTEGER,              -- ID Dorar du muhaddith
  grade_explanation     TEXT,                 -- explication du grade (explainGrade Dorar)
  grade_albani          TEXT,                 -- grade Al-Albânî si disponible
  grade_ibn_baz         TEXT,                 -- grade Ibn Bâz si disponible
  grade_ibn_uthaymin    TEXT,                 -- grade Ibn 'Uthaymîn si disponible
  grade_muqbil          TEXT,                 -- grade Muqbil ibn Hâdî si disponible
  
  -- Références canoniques
  book_name_ar          TEXT,                 -- اسم الكتاب
  book_name_fr          TEXT,                 -- nom du livre en français
  book_id_dorar         INTEGER,              -- ID livre dans Dorar (6216=Bukhâri, 3088=Muslim...)
  hadith_number         TEXT,                 -- numéro dans le livre (STRING car parfois "123a")
  hadith_id_dorar       TEXT,                 -- ID hadith dans Dorar (pour requêtes croisées)
  
  -- Analyse Sanad (5 conditions)
  sanad_ittissal        INTEGER CHECK(sanad_ittissal IN (0,1,-1)) DEFAULT -1,  -- continuité
  sanad_adalah          INTEGER CHECK(sanad_adalah IN (0,1,-1)) DEFAULT -1,   -- probité
  sanad_dabt            INTEGER CHECK(sanad_dabt IN (0,1,-1)) DEFAULT -1,     -- exactitude
  sanad_shudhudh        INTEGER CHECK(sanad_shudhudh IN (0,1,-1)) DEFAULT -1, -- absence anomalie
  sanad_illa            INTEGER CHECK(sanad_illa IN (0,1,-1)) DEFAULT -1,     -- absence défaut caché
  -- Convention: 1=OK, 0=DÉFAUT, -1=NON VÉRIFIÉ
  
  -- Métadonnées source
  source_api            TEXT,                 -- 'dorar'|'fawazahmed0'|'hadeethenc'|'manual'
  source_url            TEXT,                 -- URL direct vers la source primaire
  source_version_pin    TEXT,                 -- ex: 'v1.2.0' ou '@1' ou 'sha:abc123'
  source_data_license   TEXT CHECK(source_data_license IN ('MIT','unknown','proprietary','conditions')),
  
  -- Champs spéciaux
  has_similar           INTEGER DEFAULT 0,    -- hasSimilarHadith (Dorar)
  has_sahih_alternate   INTEGER DEFAULT 0,    -- hasAlternateHadithSahih (Dorar)
  has_usul              INTEGER DEFAULT 0,    -- hasUsulHadith (Dorar)
  has_sharh             INTEGER DEFAULT 0,    -- hasSharhMetadata (Dorar)
  sharh_id              TEXT,                 -- ID du sharh pour requête ultérieure
  takhrij               TEXT,                 -- takhriij (في كتب أخرى)
  
  -- Timestamps
  created_at            TEXT DEFAULT (datetime('now')),
  updated_at            TEXT DEFAULT (datetime('now')),
  verified_by           TEXT DEFAULT 'system', -- 'system'|'human'
  
  -- Contraintes
  CHECK (zone_id >= 1 AND zone_id <= 32)
);

-- ============================================================
-- TABLE : Rijal (biographies des narrateurs)
-- ============================================================
CREATE TABLE IF NOT EXISTS rijal (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  name_ar               TEXT NOT NULL,        -- اسم الراوي
  name_transliterated   TEXT,                 -- translittération
  name_fr               TEXT,                 -- traduction/adaptation française
  birth_year_h          INTEGER,              -- année de naissance (hijri)
  death_year_h          INTEGER,              -- année de mort (hijri)
  death_year_ce         INTEGER,              -- année de mort (grégorien)
  generation            TEXT,                 -- Sahâbi / Tâbi'î / Tâbi' al-Tâbi'în / ...
  jarh_ta_dil_grade     TEXT,                 -- grade Jarh wa Ta'dîl
  dorar_mohdith_id      INTEGER,              -- ID dans Dorar si c'est un muhaddith
  notes                 TEXT
);

-- ============================================================
-- TABLE : Tags (mots-clés, thèmes, zones)
-- ============================================================
CREATE TABLE IF NOT EXISTS entry_tags (
  entry_id              TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  tag                   TEXT NOT NULL,
  tag_type              TEXT CHECK(tag_type IN ('scholarly','thematic','zone','preacher','keyword')),
  PRIMARY KEY (entry_id, tag)
);

-- ============================================================
-- TABLE : Références croisées (CŒUR des zones 23, 27, 28)
-- ============================================================
CREATE TABLE IF NOT EXISTS cross_refs (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  source_entry_id       TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  target_type           TEXT NOT NULL CHECK(target_type IN ('zone','hadith','fatwa','quran','scholar','preacher')),
  target_id             TEXT NOT NULL,        -- ID de la cible (hadith ID, zone ID, URL fatwa, etc.)
  relation_type         TEXT CHECK(relation_type IN ('confirms','abrogates','explains','contradicts','specifies','weakens','strengthens','related')),
  relation_note         TEXT,                 -- explication de la relation
  created_at            TEXT DEFAULT (datetime('now')),
  UNIQUE (source_entry_id, target_type, target_id)
);

-- ============================================================
-- TABLE : Preachers database (Filtre des Muhaddithîn)
-- ============================================================
CREATE TABLE IF NOT EXISTS preachers (
  id                    TEXT PRIMARY KEY,     -- ex: 'sheikh-xxx'
  name_ar               TEXT NOT NULL,        -- الاسم بالعربي
  name_fr               TEXT NOT NULL,        -- nom en français
  category              TEXT CHECK(category IN ('fiable','mise_en_garde','a_eviter')),
  jarh_summary          TEXT,                 -- résumé Jarh wa Ta'dîl
  biography_fr          TEXT,
  scholar_opinions      TEXT,                 -- JSON: [{scholar, opinion, source}]
  manhaj_positions      TEXT,                 -- JSON: positions manhaj connues
  publications          TEXT,                 -- JSON: liste publications
  sources               TEXT,                 -- JSON: sources utilisées
  dorar_mohdith_id      INTEGER,              -- ID Dorar si référencé là
  created_at            TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- TABLE : Cache des requêtes Dorar (pour éviter les re-requêtes)
-- ============================================================
CREATE TABLE IF NOT EXISTS dorar_cache (
  query_hash            TEXT PRIMARY KEY,     -- MD5 de la requête normalisée
  query_params          TEXT,                 -- JSON des paramètres
  response_json         TEXT,                 -- réponse complète
  fetched_at            TEXT DEFAULT (datetime('now')),
  expires_at            TEXT                  -- TTL (ex: 7 jours)
);

-- ============================================================
-- TABLE : Zones (32 zones fixes)
-- ============================================================
CREATE TABLE IF NOT EXISTS zones (
  id                    INTEGER PRIMARY KEY,
  name                  TEXT NOT NULL UNIQUE,
  name_ar               TEXT,
  description           TEXT,
  category              TEXT, -- 'hadith_classic', 'hadith_analysis', 'doctrinal'
  created_at            TEXT DEFAULT (datetime('now')),
  updated_at            TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- TABLE : Sources (dépôts, sites, livres)
-- ============================================================
CREATE TABLE IF NOT EXISTS sources (
  id                    TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  url                   TEXT,
  type                  TEXT, -- 'github', 'website', 'book', 'fatwa_site', 'api'
  license               TEXT,
  last_access           TEXT,
  reliability_score     INTEGER DEFAULT 100, -- 0-100
  notes                 TEXT,
  created_at            TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- INDEX pour les recherches fréquentes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_entries_zone ON entries(zone_id);
CREATE INDEX IF NOT EXISTS idx_entries_grade ON entries(grade_primary);
CREATE INDEX IF NOT EXISTS idx_entries_book ON entries(book_id_dorar);
CREATE INDEX IF NOT EXISTS idx_entries_ar_clean ON entries(ar_text_clean);
CREATE INDEX IF NOT EXISTS idx_entries_fr_source ON entries(fr_source);
CREATE INDEX IF NOT EXISTS idx_cross_refs_source ON cross_refs(source_entry_id);
CREATE INDEX IF NOT EXISTS idx_cross_refs_target ON cross_refs(target_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON entry_tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_type ON entry_tags(tag_type);
CREATE INDEX IF NOT EXISTS idx_dorar_cache_expires ON dorar_cache(expires_at);

-- ============================================================
-- VUES pour statistiques
-- ============================================================
CREATE VIEW IF NOT EXISTS zone_stats AS
SELECT 
  z.id,
  z.name,
  z.name_ar,
  COUNT(e.id) as entry_count,
  AVG(CASE WHEN e.grade_primary = 'Sahih' THEN 100 
           WHEN e.grade_primary = 'Hasan' THEN 80
           WHEN e.grade_primary = 'Da''if' THEN 40
           ELSE 50 END) as avg_grade_score,
  COUNT(DISTINCT e.source_api) as source_count
FROM zones z
LEFT JOIN entries e ON z.id = e.zone_id
GROUP BY z.id, z.name, z.name_ar;

CREATE VIEW IF NOT EXISTS source_usage AS
SELECT 
  s.id,
  s.name,
  s.type,
  COUNT(e.id) as usage_count,
  s.reliability_score
FROM sources s
LEFT JOIN entries e ON s.id = e.source_api
GROUP BY s.id, s.name, s.type, s.reliability_score
ORDER BY usage_count DESC;

-- ============================================================
-- INSERTION DES 32 ZONES (définition complète V7.0)
-- ============================================================
INSERT OR IGNORE INTO zones (id, name, name_ar, description, category) VALUES
-- Zones 1-10 : Sciences de l'Isnad et du Matn
(1, 'Isnad', 'الإسناد', 'La chaîne complète des transmetteurs du hadith', 'hadith_classic'),
(2, 'Matn', 'المتن', 'Le texte du hadith sans l''isnad', 'hadith_classic'),
(3, 'Tarjîh', 'الترجيح', 'Arbitrage entre hadiths contradictoires apparents', 'hadith_classic'),
(4, 'Takhrîj', 'التخريج', 'Identification des sources où le hadith apparaît', 'hadith_classic'),
(5, 'Ilal', 'العلل', 'Défauts subtils qui affaiblissent un hadith', 'hadith_classic'),
(6, 'Shurûh', 'الشروح', 'Explications et commentaires des savants', 'hadith_classic'),
(7, 'Naskh', 'الناسخ والمنسوخ', 'Hadiths abrogés par d''autres hadiths ou versets', 'hadith_classic'),
(8, 'Mukhtalif al-Hadith', 'مختلف الحديث', 'Hadiths d''apparence contradictoire et leur réconciliation', 'hadith_classic'),
(9, 'Qawâ''id', 'القواعد الحديثية', 'Principes méthodologiques des sciences du hadith', 'hadith_classic'),
(10, 'Rijal', 'علم الرجال', 'Science des biographies des transmetteurs', 'hadith_classic'),

-- Zones 11-20 : Grades et Classification
(11, 'Grading', 'الحكم العام', 'Vue d''ensemble du statut d''authenticité', 'hadith_analysis'),
(12, 'Sahîh', 'صحيح', 'Authentique — 5 conditions de l''isnad remplies', 'hadith_analysis'),
(13, 'Hasan', 'حسن', 'Bon — légèrement inférieur au Sahîh', 'hadith_analysis'),
(14, 'Da''îf', 'ضعيف', 'Faible — 1 ou + conditions non remplies', 'hadith_analysis'),
(15, 'Mawdû''', 'موضوع', 'Fabriqué — inventé, jamais dit par le Prophète ﷺ', 'hadith_analysis'),
(16, 'Mutawâtir', 'متواتر', 'Transmis par un nombre si grand qu''il exclut toute erreur', 'hadith_analysis'),
(17, 'Âhâd', 'آحاد', 'Transmis par un nombre restreint de narrateurs', 'hadith_analysis'),
(18, 'Mursal / Munqati''', 'المرسل / المنقطع', 'Isnad avec rupture ou manque de lien au Compagnon', 'hadith_analysis'),
(19, 'Musnad Ahmad', 'مسند أحمد', 'Hadiths du Musnad Ahmad avec particularités propres', 'hadith_analysis'),
(20, 'Silsilah Al-Albânî', 'سلسلة الألباني', 'Hadith gradé dans la Silsilah As-Sahîhah ou Ad-Da''îfah', 'hadith_analysis'),

-- Zones 21-32 : Zones thématiques et analytiques
(21, 'Aqîdah', 'العقيدة', 'Hadith relatifs aux fondements de la croyance islamique', 'doctrinal'),
(22, 'Fiqh al-''Ibâdât', 'فقه العبادات', 'Hadiths sur les actes d''adoration (salat, zakat, sawm, hajj)', 'doctrinal'),
(23, 'Mu''âmalât', 'المعاملات', 'Hadiths sur les transactions et relations sociales', 'doctrinal'),
(24, 'Hadith Qudsî', 'الحديث القدسي', 'Paroles divines rapportées par le Prophète ﷺ', 'doctrinal'),
(25, 'Âthâr as-Sahâbah', 'آثار الصحابة', 'Paroles et actes des Compagnons (non prophétiques)', 'doctrinal'),
(26, 'Nawâhî', 'النواهي', 'Hadiths portant sur les interdictions islamiques', 'doctrinal'),
(27, 'Fadâ''il', 'الفضائل', 'Hadiths sur les vertus des actes et des personnes', 'doctrinal'),
(28, 'Dhikr et Du''â''', 'الذكر والدعاء', 'Invocations et formules de remembrance', 'doctrinal'),
(29, 'Zuhd et Raqâ''iq', 'الزهد والرقائق', 'Hadiths sur le détachement du monde et l''attendrissement du cœur', 'doctrinal'),
(30, 'Fatâwâ Salafiyyah', 'الفتاوى السلفية', 'Fatwas des savants du Salaf as-Sâlih liées aux hadiths', 'doctrinal'),
(31, 'Manâqib et Sîrah', 'المناقب والسيرة', 'Qualités et biographie du Prophète ﷺ', 'doctrinal'),
(32, 'Hadith Fabricado', 'الحديث الموضوع — تحذير', 'Hadiths fabriqués circulant sur les réseaux', 'doctrinal');