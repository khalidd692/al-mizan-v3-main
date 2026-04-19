-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRATION 004: TAXONOMIE COMPLÈTE DES ḤUKM (25 CLASSES)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Date: 2026-04-19
-- Objectif: Implémenter les 25 classes de ḥukm des muḥaddithīn
-- Prérequis: Migrations 001-003 appliquées
-- ═══════════════════════════════════════════════════════════════════════════════

-- Table de référence pour les ~25 classes de ḥukm classiques
CREATE TABLE IF NOT EXISTS hukm_classes (
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

-- ═══════════════════════════════════════════════════════════════════════════════
-- MAQBŪL (المقبول) — Acceptés pour l'action
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('sahih_li_dhatihi',     'صحيح لذاته',     'Authentique en soi',                       'maqbul', 'accepté_fort',  10, 1, 'ahkam',   'سند متصل بنقل عدل تام الضبط عن مثله غير شاذ ولا معلل', 'Chaîne continue, narrateurs justes, mémoire parfaite, ni shādh ni muʿall'),
('sahih_li_ghayrihi',    'صحيح لغيره',     'Authentique par soutien',                  'maqbul', 'accepté_fort',   9, 1, 'ahkam',   'حسن لذاته تعددت طرقه فارتقى', 'Ḥasan li-dhātihi élevé par multiplicité de chaînes'),
('hasan_li_dhatihi',     'حسن لذاته',      'Bon en soi',                               'maqbul', 'accepté_fort',   8, 1, 'ahkam',   'اتصال سند ورواة عدول خف ضبط أحدهم', 'Chaîne continue, narrateurs justes, mémoire d''un rāwī légèrement affaiblie'),
('hasan_li_ghayrihi',    'حسن لغيره',      'Bon par soutien',                          'maqbul', 'accepté_faible', 7, 1, 'ahkam',   'ضعيف تعددت طرقه فتقوى', 'Faible originel élevé par multiplicité de chaînes corroborantes'),
('hasan_sahih',          'حسن صحيح',       'Bon-authentique (Tirmidhī)',               'maqbul', 'accepté_fort',   9, 1, 'ahkam',   'مصطلح الترمذي للجمع بين الحسن والصحيح', 'Terme spécifique à al-Tirmidhī'),
('maskut_ʿanh_abu_dawud','مسكوت عنه عند أبي داود','Silence d''Abū Dāwūd',               'maqbul', 'accepté_faible', 6, 1, 'fadail',  'سكت عنه أبو داود في سننه', 'Silence d''Abū Dāwūd dans ses Sunan, indique l''acceptabilité selon lui');

-- ═══════════════════════════════════════════════════════════════════════════════
-- DAʿĪF (الضعيف) — Rejeté général et sous-types par cause
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('daif',                 'ضعيف',           'Faible',                                   'mardud', 'rejeté_general', 4, 0, 'aucun',   'فقد شرطا من شروط القبول', 'A perdu un des critères d''acceptation'),
('daif_jiddan',          'ضعيف جدا',       'Très faible',                              'mardud', 'rejeté_general', 2, 0, 'aucun',   'ضعيف لا ينجبر بالشواهد', 'Faiblesse irrécupérable par soutiens');

-- ═══════════════════════════════════════════════════════════════════════════════
-- Rejeté par défaut du SANAD (continuité)
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('muʿallaq',             'معلق',           'Suspendu (début omis)',                    'mardud', 'rejeté_sanad',   3, 0, 'aucun',   'حذف من مبدأ إسناده راو أو أكثر', 'Un ou plusieurs narrateurs omis au début du sanad'),
('mursal',               'مرسل',           'Envoyé (compagnon omis)',                  'mardud', 'rejeté_sanad',   3, 0, 'aucun',   'قول التابعي: قال رسول الله ﷺ', 'Le Tābiʿī attribue directement au Prophète sans mentionner le Ṣaḥābī'),
('munqatiʿ',             'منقطع',          'Rompu (un maillon central)',               'mardud', 'rejeté_sanad',   3, 0, 'aucun',   'سقط من وسط إسناده راو واحد', 'Un narrateur manquant au milieu'),
('muʿdal',               'معضل',           'Difficile (2+ maillons)',                  'mardud', 'rejeté_sanad',   2, 0, 'aucun',   'سقط من إسناده اثنان فأكثر على التوالي', '2 narrateurs ou plus consécutifs manquants'),
('mudallas',             'مدلس',           'Masqué (tadlīs)',                          'mardud', 'rejeté_sanad',   4, 0, 'aucun',   'رواية الراوي عمن عاصره بما يوهم السماع ولم يسمع', 'Le narrateur rapporte d''un contemporain en laissant supposer une écoute directe qu''il n''a pas eue');

-- ═══════════════════════════════════════════════════════════════════════════════
-- Rejeté par défaut du RĀWĪ
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('munkar',               'منكر',           'Désapprouvé',                              'mardud', 'rejeté_rawi',    2, 0, 'aucun',   'تفرد الضعيف بما يخالف الثقات', 'Rāwī faible seul à rapporter contre les fiables'),
('shadhdh',              'شاذ',            'Anormal',                                  'mardud', 'rejeté_rawi',    3, 0, 'aucun',   'مخالفة الثقة لمن هو أوثق منه', 'Un thiqah contredit plus fiable que lui'),
('matruk',               'متروك',          'Abandonné',                                'mardud', 'rejeté_rawi',    1, 0, 'aucun',   'ما انفرد به المتهم بالكذب', 'Seul rapporteur accusé de mensonge'),
('mawduʿ',               'موضوع',          'Forgé',                                    'mardud', 'rejeté_rawi',    0, 0, 'aucun',   'المكذوب المختلق على رسول الله ﷺ', 'Mensonge forgé attribué au Prophète'),
('la_asla_lah',          'لا أصل له',      'Sans fondement',                           'mardud', 'rejeté_rawi',    0, 0, 'aucun',   'لا يوجد له سند يعتمد عليه', 'Aucune chaîne sur laquelle s''appuyer'),
('batil',                'باطل',           'Nul et faux',                              'mardud', 'rejeté_rawi',    0, 0, 'aucun',   'مخترع مكذوب', 'Inventé et faux');

-- ═══════════════════════════════════════════════════════════════════════════════
-- Rejeté par ALTÉRATION du texte ou chaîne
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('muʿallal',             'معلل / معل',     'Avec défaut caché',                        'mardud', 'altération',     3, 0, 'aucun',   'حديث ظاهره الصحة وباطنه علة قادحة', 'Hadith en apparence authentique mais porteur d''une ʿillah invalidante'),
('mudraj',               'مدرج',           'Interpolé',                                'mardud', 'altération',     3, 0, 'aucun',   'أدخل في متنه ما ليس منه', 'Quelque chose d''extérieur a été inséré dans le matn'),
('maqlub',               'مقلوب',          'Inversé',                                  'mardud', 'altération',     3, 0, 'aucun',   'تبديل راو بآخر أو متن بآخر', 'Un narrateur ou un matn échangé avec un autre'),
('mudtarib',             'مضطرب',          'Confus',                                   'mardud', 'altération',     2, 0, 'aucun',   'روي على أوجه متعارضة لا ترجيح بينها', 'Rapporté de façons contradictoires sans pouvoir trancher'),
('musahhaf',             'مصحف',           'Erreur de diacritiques',                   'mardud', 'altération',     3, 0, 'aucun',   'تغير بتغيير النقط مع بقاء الحروف', 'Altération par changement des points diacritiques'),
('muharraf',             'محرف',           'Erreur de voyelles',                       'mardud', 'altération',     3, 0, 'aucun',   'تغير بتغيير الشكل مع بقاء الحروف', 'Altération par changement des voyelles'),
('mazid_muttasil',       'مزيد في متصل الأسانيد', 'Maillon ajouté',                     'mardud', 'altération',     4, 0, 'aucun',   'زيادة راو في سند متصل', 'Un narrateur ajouté dans une chaîne connectée');

-- ═══════════════════════════════════════════════════════════════════════════════
-- Jahālah (inconnu)
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('majhul_al_ʿayn',       'مجهول العين',    'Inconnu en identité',                      'mardud', 'jahalah',        2, 0, 'aucun',   'لم يرو عنه إلا واحد ولم يوثق', 'Un seul rāwī rapporte de lui, et il n''est pas authentifié'),
('majhul_al_hal',        'مجهول الحال',    'Inconnu en état (mastūr)',                 'mardud', 'jahalah',        3, 0, 'aucun',   'روى عنه اثنان فصاعدا ولم يوثق', 'Rapporté par 2+ mais jamais authentifié');

-- ═══════════════════════════════════════════════════════════════════════════════
-- TYPOLOGIE (orthogonale : s'ajoute au ḥukm de base)
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('mutawatir',            'متواتر',         'Multi-transmis massif',                    'typologie', 'quantitatif', 10, 1, 'ahkam',  'رواه جمع يستحيل تواطؤهم على الكذب', 'Rapporté par un grand nombre rendant impossible la connivence mensongère'),
('mashhur',              'مشهور',          'Célèbre',                                  'typologie', 'quantitatif',  8, 1, 'ahkam',  'ما رواه ثلاثة فأكثر دون التواتر', 'Rapporté par 3+ sans atteindre le tawātur'),
('ʿaziz',                'عزيز',           'Rare (2 chaînes)',                         'typologie', 'quantitatif',  7, 1, 'ahkam',  'ما رواه اثنان في جميع طبقات السند', 'Rapporté par 2 dans toutes les ṭabaqāt'),
('gharib',               'غريب',           'Isolé (1 chaîne)',                         'typologie', 'quantitatif',  5, 1, 'ahkam',  'ما تفرد به راو واحد', 'Seul un rāwī le rapporte');

-- ═══════════════════════════════════════════════════════════════════════════════
-- META (statut de vérification Mîzân)
-- ═══════════════════════════════════════════════════════════════════════════════
INSERT OR IGNORE INTO hukm_classes VALUES
('mukhtalaf_fih',        'مختلف فيه',      'Disputé entre imams',                      'meta',   'divergence',     5, 0, 'fadail',   'اختلف العلماء في حكمه', 'Divergence entre imams sur le verdict'),
('tawaqquf',             'متوقف فيه',      'Jugement suspendu',                        'meta',   'divergence',     5, 0, 'aucun',   'لم يترجح للعالم حكم', 'L''imam n''a pas pu trancher'),
('lam_yuhaqqaq',         'لم يحقق بعد',    'Non encore vérifié',                       'meta',   'pending',        5, 0, 'aucun',   'لم يدرس إسناده بعد', 'Chaîne non étudiée à ce jour');

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEX ET CONTRAINTES
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_hukm_classes_category ON hukm_classes(category);
CREATE INDEX IF NOT EXISTS idx_hukm_classes_severity ON hukm_classes(severity);
CREATE INDEX IF NOT EXISTS idx_hukm_classes_can_act ON hukm_classes(can_be_acted_upon);

-- ═══════════════════════════════════════════════════════════════════════════════
-- VALIDATION : Vérifier que toutes les 25 classes sont présentes
-- ═══════════════════════════════════════════════════════════════════════════════
-- Cette requête doit retourner 25
SELECT COUNT(*) AS total_classes FROM hukm_classes;

-- Distribution par catégorie (doit retourner 4 lignes)
SELECT category, COUNT(*) AS count FROM hukm_classes GROUP BY category ORDER BY category;

-- ═══════════════════════════════════════════════════════════════════════════════
-- FIN DE LA MIGRATION 004
-- ═══════════════════════════════════════════════════════════════════════════════
