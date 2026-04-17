-- SCHÉMA SQL AL-MĪZĀN V6.0
-- Base de données académique Salafi pour 32 zones

-- Table des zones (32 zones fixes)
CREATE TABLE IF NOT EXISTS zones (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  name_ar TEXT,
  description TEXT,
  category TEXT, -- 'hadith_classic', 'hadith_analysis', 'doctrinal'
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Table des sources (dépôts, sites, livres)
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT,
  type TEXT, -- 'github', 'website', 'book', 'fatwa_site'
  license TEXT,
  last_access TEXT,
  reliability_score INTEGER DEFAULT 100, -- 0-100
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Table principale des entrées (hadiths, fatwas, commentaires)
CREATE TABLE IF NOT EXISTS entries (
  id TEXT PRIMARY KEY, -- UUID v4
  zone_id INTEGER NOT NULL REFERENCES zones(id),
  source_id TEXT NOT NULL REFERENCES sources(id),
  
  -- Contenu textuel
  arabic_text TEXT,
  fr_summary TEXT,
  english_text TEXT,
  
  -- Référence exacte
  source_reference TEXT NOT NULL, -- Ex: "Sahih al-Bukhari, Livre 1, Hadith 2"
  book_name TEXT,
  chapter_name TEXT,
  hadith_number TEXT,
  
  -- Classification
  keywords TEXT, -- JSON array
  scholarly_tags TEXT, -- JSON array
  
  -- Grading (authentification)
  grading TEXT, -- 'sahih', 'hasan', 'daif', 'mawdu', etc.
  grader TEXT, -- Nom du savant
  grading_source TEXT, -- Référence exacte du tahqiq
  grading_note TEXT,
  
  -- Métadonnées de confiance
  confidence INTEGER DEFAULT 50, -- 0-100
  tawaqquf BOOLEAN DEFAULT FALSE,
  tawaqquf_reason TEXT,
  
  -- Annotations savantes
  notes TEXT,
  scholarly_commentary TEXT,
  
  -- Métadonnées système
  version TEXT DEFAULT 'V6.0',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  
  -- Contraintes
  CHECK (confidence >= 0 AND confidence <= 100),
  CHECK (zone_id >= 1 AND zone_id <= 32)
);

-- Table des tags (pour recherche avancée)
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  name_ar TEXT,
  category TEXT, -- 'aqidah', 'fiqh', 'usul', 'hadith_science'
  description TEXT
);

-- Table de liaison entries-tags
CREATE TABLE IF NOT EXISTS entry_tags (
  entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (entry_id, tag_id)
);

-- Table des références croisées
CREATE TABLE IF NOT EXISTS cross_refs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  ref_type TEXT NOT NULL, -- 'zone', 'hadith', 'fatwa', 'commentary'
  ref_id TEXT NOT NULL,
  ref_description TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Table des savants (pour référence)
CREATE TABLE IF NOT EXISTS scholars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  name_ar TEXT,
  birth_year INTEGER,
  death_year INTEGER,
  school TEXT, -- 'salafi', 'hanbali', etc.
  specialization TEXT,
  reliability_level TEXT, -- 'thiqa', 'saduq', etc.
  bio TEXT
);

-- Table des chaînes de transmission (isnad)
CREATE TABLE IF NOT EXISTS isnad_chains (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id TEXT NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
  chain_text TEXT NOT NULL,
  chain_grade TEXT,
  narrators TEXT, -- JSON array des noms
  notes TEXT
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_entries_zone ON entries(zone_id);
CREATE INDEX IF NOT EXISTS idx_entries_source ON entries(source_id);
CREATE INDEX IF NOT EXISTS idx_entries_grading ON entries(grading);
CREATE INDEX IF NOT EXISTS idx_entries_confidence ON entries(confidence);
CREATE INDEX IF NOT EXISTS idx_entries_tawaqquf ON entries(tawaqquf);
CREATE INDEX IF NOT EXISTS idx_cross_refs_entry ON cross_refs(entry_id);
CREATE INDEX IF NOT EXISTS idx_entry_tags_entry ON entry_tags(entry_id);
CREATE INDEX IF NOT EXISTS idx_entry_tags_tag ON entry_tags(tag_id);

-- Vue pour statistiques par zone
CREATE VIEW IF NOT EXISTS zone_stats AS
SELECT 
  z.id,
  z.name,
  COUNT(e.id) as entry_count,
  AVG(e.confidence) as avg_confidence,
  SUM(CASE WHEN e.tawaqquf = 1 THEN 1 ELSE 0 END) as tawaqquf_count,
  COUNT(DISTINCT e.source_id) as source_count
FROM zones z
LEFT JOIN entries e ON z.id = e.zone_id
GROUP BY z.id, z.name;

-- Vue pour sources les plus utilisées
CREATE VIEW IF NOT EXISTS source_usage AS
SELECT 
  s.id,
  s.name,
  s.type,
  COUNT(e.id) as usage_count,
  AVG(e.confidence) as avg_confidence
FROM sources s
LEFT JOIN entries e ON s.id = e.source_id
GROUP BY s.id, s.name, s.type
ORDER BY usage_count DESC;

-- Insertion des 32 zones
INSERT OR IGNORE INTO zones (id, name, name_ar, description, category) VALUES
(1, 'Isnad', 'الإسناد', 'Chaînes de transmission', 'hadith_classic'),
(2, 'Matn', 'المتن', 'Texte du hadith', 'hadith_classic'),
(3, 'Tarjih', 'الترجيح', 'Préférence entre avis', 'hadith_classic'),
(4, 'Takhrij', 'التخريج', 'Extraction et référencement', 'hadith_classic'),
(5, 'Ilal', 'العلل', 'Défauts cachés', 'hadith_classic'),
(6, 'Shuruh', 'الشروح', 'Commentaires savants', 'hadith_classic'),
(7, 'Naskh', 'النسخ', 'Abrogation', 'hadith_classic'),
(8, 'Mukhtalif', 'مختلف الحديث', 'Hadiths apparemment contradictoires', 'hadith_classic'),
(9, 'Qawaid', 'القواعد', 'Règles méthodologiques', 'hadith_classic'),
(10, 'Fawaid', 'الفوائد', 'Bénéfices et enseignements', 'hadith_classic'),
(11, 'Grading', 'التصحيح والتضعيف', 'Authentification générale', 'hadith_analysis'),
(12, 'Sahih', 'الصحيح', 'Hadiths authentiques', 'hadith_analysis'),
(13, 'Daif', 'الضعيف', 'Hadiths faibles', 'hadith_analysis'),
(14, 'Hasan', 'الحسن', 'Hadiths bons', 'hadith_analysis'),
(15, 'Mutawatir', 'المتواتر', 'Hadiths notoires', 'hadith_analysis'),
(16, 'Ahad', 'الآحاد', 'Hadiths isolés', 'hadith_analysis'),
(17, 'Mawdu', 'الموضوع', 'Hadiths forgés', 'hadith_analysis'),
(18, 'Munkar', 'المنكر', 'Hadiths rejetés', 'hadith_analysis'),
(19, 'Shadh', 'الشاذ', 'Hadiths irréguliers', 'hadith_analysis'),
(20, 'Maqlub', 'المقلوب', 'Hadiths inversés', 'hadith_analysis'),
(21, 'Aqidah', 'العقيدة', 'Croyance islamique', 'doctrinal'),
(22, 'Fawaid_Extended', 'الفوائد الموسعة', 'Bénéfices étendus', 'doctrinal'),
(23, 'Tarjih_Doctrinal', 'الترجيح العقدي', 'Préférence doctrinale', 'doctrinal'),
(24, 'Shuruh_Savants', 'شروح العلماء', 'Commentaires des savants', 'doctrinal'),
(25, 'Naskh_Documented', 'النسخ الموثق', 'Abrogation documentée', 'doctrinal'),
(26, 'Ilal_Advanced', 'العلل المتقدمة', 'Défauts avancés', 'doctrinal'),
(27, 'Takhrij_Complete', 'التخريج الكامل', 'Extraction complète', 'doctrinal'),
(28, 'Mukhtalif_Hadith', 'مختلف الحديث', 'Résolution des contradictions', 'doctrinal'),
(29, 'Qawaid_Fiqh', 'القواعد الفقهية', 'Règles jurisprudentielles', 'doctrinal'),
(30, 'Fatawa_Salafiyyah', 'الفتاوى السلفية', 'Fatwas salafies', 'doctrinal'),
(31, 'Manaqib_Sirah', 'المناقب والسيرة', 'Mérites et biographie', 'doctrinal'),
(32, 'Glossaire_Termes', 'المصطلحات', 'Glossaire technique', 'doctrinal');