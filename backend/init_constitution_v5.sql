-- ════════════════════════════════════════════════════════════════════════════
-- AL-MĪZĀN v5.0 — SCHÉMA DDL COMPLET SELON CONSTITUTION
-- Référence éthique suprême : Constitution_v4 (2).md
-- ════════════════════════════════════════════════════════════════════════════

-- Table principale des hadiths avec Sanad Numérique (SHA256)
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
    grade_final     TEXT NOT NULL,                 -- Sahih | Hasan | Da'if | etc.
    categorie       TEXT NOT NULL,                 -- MAQBUL | DAIF | MAWDUU
    badge_alerte    INTEGER DEFAULT 0,             -- 1 = Mawdū' (rouge obligatoire)
    source_url      TEXT,
    source_api      TEXT,                          -- "dorar_json" | "hadeethenc"
    inserted_at     TEXT DEFAULT (datetime('now'))
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_hadiths_sha256 ON hadiths(sha256);
CREATE INDEX IF NOT EXISTS idx_hadiths_collection ON hadiths(collection);
CREATE INDEX IF NOT EXISTS idx_hadiths_categorie ON hadiths(categorie);
CREATE INDEX IF NOT EXISTS idx_hadiths_grade ON hadiths(grade_final);

-- Table des avis des savants (WHITELIST stricte)
CREATE TABLE IF NOT EXISTS avis_savants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hadith_sha256   TEXT NOT NULL REFERENCES hadiths(sha256),
    savant          TEXT NOT NULL,                 -- voir WHITELIST Constitution
    epoque          TEXT NOT NULL,                 -- MUTAQADDIMUN | KHALAF | MUASIR
    jugement        TEXT NOT NULL,                 -- texte du hukm
    source_jugement TEXT
);

CREATE INDEX IF NOT EXISTS idx_avis_sha256 ON avis_savants(hadith_sha256);
CREATE INDEX IF NOT EXISTS idx_avis_savant ON avis_savants(savant);

-- Lexique de Fer (Attributs d'Allah — NON NÉGOCIABLE)
CREATE TABLE IF NOT EXISTS lexique_fer (
    terme_ar TEXT PRIMARY KEY,
    terme_fr TEXT NOT NULL,
    interdit TEXT NOT NULL  -- la traduction interdite (ta'wil)
);

-- Insertion du Lexique de Fer (Constitution Section I-3)
INSERT OR IGNORE INTO lexique_fer (terme_ar, terme_fr, interdit) VALUES
    ('استوى',  'S''est établi (par Son Essence)',        'S''est installé / a pris le contrôle'),
    ('يد',     'Main (réelle, sans comparaison)',         'Puissance / Grâce'),
    ('نزول',   'Descend (comme Il le mérite)',            'Sa miséricorde descend'),
    ('وجه',    'Visage (réel, sans comparaison)',         'Essence / Être'),
    ('ساق',    'Jambe (réelle, sans comparaison)',        'Sévérité / Épreuve'),
    ('عين',    'Œil/Regard (réel, sans comparaison)',     'Connaissance / Surveillance'),
    ('غضب',    'Colère (réelle d''Allah)',                'État émotionnel métaphorique'),
    ('محبة',   'Amour (réel d''Allah)',                   'Volonté de récompenser'),
    ('فوق',    'Au-dessus (réel, sur Son Trône)',         'Supériorité en rang');

-- Table de logs d'erreurs
CREATE TABLE IF NOT EXISTS errors_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now')),
    error_type  TEXT NOT NULL,  -- TAAWIL_DETECTED | SOURCE_INTERDITE | API_ERROR
    sha256      TEXT,
    details     TEXT,
    resolved    INTEGER DEFAULT 0
);

-- Vue pour statistiques rapides
CREATE VIEW IF NOT EXISTS stats_corpus AS
SELECT 
    collection,
    categorie,
    grade_final,
    COUNT(*) as total,
    SUM(CASE WHEN badge_alerte = 1 THEN 1 ELSE 0 END) as mawduu_count
FROM hadiths
GROUP BY collection, categorie, grade_final;

-- ════════════════════════════════════════════════════════════════════════════
-- VÉRIFICATION DE L'INTÉGRITÉ
-- ════════════════════════════════════════════════════════════════════════════

-- Contrainte : Aucun hadith sans matn_ar
CREATE TRIGGER IF NOT EXISTS check_matn_ar_not_empty
BEFORE INSERT ON hadiths
FOR EACH ROW
WHEN NEW.matn_ar IS NULL OR trim(NEW.matn_ar) = ''
BEGIN
    SELECT RAISE(ABORT, 'VIOLATION CONSTITUTION: matn_ar ne peut être vide');
END;

-- Contrainte : badge_alerte = 1 si grade_final = Mawdu' ou Batil
CREATE TRIGGER IF NOT EXISTS enforce_mawduu_badge
BEFORE INSERT ON hadiths
FOR EACH ROW
WHEN (NEW.grade_final = 'Mawdu''' OR NEW.grade_final = 'Batil') AND NEW.badge_alerte != 1
BEGIN
    SELECT RAISE(ABORT, 'VIOLATION CONSTITUTION: Mawdu''/Batil exige badge_alerte=1');
END;

-- Contrainte : source_api doit être whitelistée
CREATE TRIGGER IF NOT EXISTS check_source_api
BEFORE INSERT ON hadiths
FOR EACH ROW
WHEN NEW.source_api NOT IN ('dorar_json', 'hadeethenc', 'manual_verified')
BEGIN
    SELECT RAISE(ABORT, 'VIOLATION CONSTITUTION: source_api non autorisée');
END;