-- ============================================================================
-- MIGRATION 003 : SEED COMPLET DES MUḤADDITHĪN (~80 IMAMS)
-- ============================================================================
-- Conforme au BRIEF v2 - PARTIE C
-- Classification par ṭabaqah avec poids de fiabilité
-- ============================================================================

-- Supprimer les seeds v1 (re-peupler proprement)
DELETE FROM hukm_sources;

-- Note: Les colonnes tabaqah, death_hijri, specialty doivent déjà exister
-- depuis la migration 001_verifier_schema_almizane.sql
-- Si elles n'existent pas, cette migration échouera et il faudra les ajouter manuellement

-- ────────────────────────────────────────────────────────────────────────────
-- MUTAQADDIMŪN (avant 300 H)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO hukm_sources (name_ar, name_fr, era, manhaj, death_hijri, tabaqah, specialty, reliability_weight) VALUES
('مالك بن أنس', 'Mālik ibn Anas', 'classical', 'ahl_al_hadith', 179, 'mutaqaddim', 'rijal_madina', 1.0),
('شعبة بن الحجاج', 'Shuʿbah ibn al-Ḥajjāj', 'classical', 'ahl_al_hadith', 160, 'mutaqaddim', 'rijal_ʿilal', 1.0),
('سفيان الثوري', 'Sufyān al-Thawrī', 'classical', 'ahl_al_hadith', 161, 'mutaqaddim', 'rijal', 1.0),
('عبدالرحمن بن مهدي', 'ʿAbd al-Raḥmān ibn Mahdī', 'classical', 'ahl_al_hadith', 198, 'mutaqaddim', 'ʿilal', 1.0),
('يحيى بن سعيد القطان', 'Yaḥyā ibn Saʿīd al-Qaṭṭān', 'classical', 'ahl_al_hadith', 198, 'mutaqaddim', 'ʿilal_rijal', 1.0),
('الشافعي', 'al-Shāfiʿī', 'classical', 'ahl_al_hadith', 204, 'mutaqaddim', 'usul', 0.95),
('علي بن المديني', 'ʿAlī ibn al-Madīnī', 'classical', 'ahl_al_hadith', 234, 'mutaqaddim', 'ʿilal', 1.0),
('يحيى بن معين', 'Yaḥyā ibn Maʿīn', 'classical', 'ahl_al_hadith', 233, 'mutaqaddim', 'jarh_taʿdil', 1.0),
('أحمد بن حنبل', 'Aḥmad ibn Ḥanbal', 'classical', 'ahl_al_hadith', 241, 'mutaqaddim', 'ʿilal_musnad', 1.0),
('إسحاق بن راهويه', 'Isḥāq ibn Rāhawayh', 'classical', 'ahl_al_hadith', 238, 'mutaqaddim', 'fiqh_hadith', 0.95),
('ابن أبي شيبة', 'Ibn Abī Shaybah', 'classical', 'ahl_al_hadith', 235, 'mutaqaddim', 'musannaf', 0.9),
('ابن سعد', 'Ibn Saʿd', 'classical', 'ahl_al_hadith', 230, 'mutaqaddim', 'tabaqat', 0.9),
('الدارمي', 'al-Dārimī', 'classical', 'ahl_al_hadith', 255, 'mutaqaddim', 'sunan', 0.9),
('البخاري', 'al-Bukhārī', 'classical', 'ahl_al_hadith', 256, 'mutaqaddim', 'sahih_tarikh', 1.0),
('مسلم بن الحجاج', 'Muslim ibn al-Ḥajjāj', 'classical', 'ahl_al_hadith', 261, 'mutaqaddim', 'sahih_ʿilal', 1.0),
('أبو داود السجستاني', 'Abū Dāwūd al-Sijistānī', 'classical', 'ahl_al_hadith', 275, 'mutaqaddim', 'sunan_rijal', 0.95),
('أبو زرعة الرازي', 'Abū Zurʿah al-Rāzī', 'classical', 'ahl_al_hadith', 264, 'mutaqaddim', 'jarh_ʿilal', 1.0),
('أبو حاتم الرازي', 'Abū Ḥātim al-Rāzī', 'classical', 'ahl_al_hadith', 277, 'mutaqaddim', 'jarh_ʿilal', 1.0),
('الجوزجاني', 'al-Jūzajānī', 'classical', 'ahl_al_hadith', 259, 'mutaqaddim', 'jarh', 0.9),
('العجلي', 'al-ʿIjlī', 'classical', 'ahl_al_hadith', 261, 'mutaqaddim', 'thiqat', 0.9),
('الترمذي', 'al-Tirmidhī', 'classical', 'ahl_al_hadith', 279, 'mutaqaddim', 'sunan_ʿilal', 0.95),
('يعقوب الفسوي', 'Yaʿqūb al-Fasawī', 'classical', 'ahl_al_hadith', 277, 'mutaqaddim', 'tarikh', 0.9),
('البزار', 'al-Bazzār', 'classical', 'ahl_al_hadith', 292, 'mutaqaddim', 'musnad_ʿilal', 0.9),
('النسائي', 'al-Nasāʾī', 'classical', 'ahl_al_hadith', 303, 'mutaqaddim', 'sunan_rijal', 0.95),
('ابن خزيمة', 'Ibn Khuzaymah', 'classical', 'ahl_al_hadith', 311, 'mutaqaddim', 'sahih', 0.9),
('ابن أبي حاتم', 'Ibn Abī Ḥātim al-Rāzī', 'classical', 'ahl_al_hadith', 327, 'mutaqaddim', 'jarh_ʿilal', 1.0),
('أبو عوانة', 'Abū ʿAwānah al-Isfarāyīnī', 'classical', 'ahl_al_hadith', 316, 'mutaqaddim', 'mustakhraj', 0.85),
('الطحاوي', 'al-Ṭaḥāwī', 'classical', 'ahl_al_hadith', 321, 'mutaqaddim', 'mushkil', 0.9),
('العقيلي', 'al-ʿUqaylī', 'classical', 'ahl_al_hadith', 322, 'mutaqaddim', 'duʿafa', 0.9),
('ابن حبان', 'Ibn Ḥibbān al-Bustī', 'classical', 'ahl_al_hadith', 354, 'mutaqaddim', 'sahih_thiqat', 0.85),
('ابن عدي', 'Ibn ʿAdī al-Jurjānī', 'classical', 'ahl_al_hadith', 365, 'mutaqaddim', 'kamil_duʿafa', 0.95),
('الطبراني', 'al-Ṭabarānī', 'classical', 'ahl_al_hadith', 360, 'mutaqaddim', 'maʿajim', 0.85),
('الدارقطني', 'al-Dāraqutnī', 'classical', 'ahl_al_hadith', 385, 'mutaqaddim', 'ʿilal_sunan', 1.0),
('الحاكم', 'al-Ḥākim al-Naysābūrī', 'classical', 'ahl_al_hadith', 405, 'mutaqaddim', 'mustadrak', 0.75),
('ابن مندة', 'Ibn Mandah', 'classical', 'ahl_al_hadith', 395, 'mutaqaddim', 'rijal', 0.85),
('أبو نعيم الأصبهاني', 'Abū Nuʿaym al-Aṣbahānī', 'classical', 'ahl_al_hadith', 430, 'mutaqaddim', 'hilyah', 0.85);

-- ────────────────────────────────────────────────────────────────────────────
-- MUTAWASSIṬŪN (400-700 H)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO hukm_sources (name_ar, name_fr, era, manhaj, death_hijri, tabaqah, specialty, reliability_weight) VALUES
('البيهقي', 'al-Bayhaqī', 'classical', 'ahl_al_hadith', 458, 'mutawassit', 'sunan_kubra', 0.95),
('الخطيب البغدادي', 'al-Khaṭīb al-Baghdādī', 'classical', 'ahl_al_hadith', 463, 'mutawassit', 'kifayah_tarikh', 0.95),
('ابن عبدالبر', 'Ibn ʿAbd al-Barr', 'classical', 'ahl_al_hadith', 463, 'mutawassit', 'istidhkar_tamhid', 0.9),
('ابن حزم', 'Ibn Ḥazm al-Ẓāhirī', 'classical', 'ahl_al_hadith', 456, 'mutawassit', 'muhalla', 0.85),
('القاضي عياض', 'al-Qāḍī ʿIyāḍ', 'classical', 'ahl_al_hadith', 544, 'mutawassit', 'ikmal_ilmaʿ', 0.9),
('ابن الجوزي', 'Ibn al-Jawzī', 'classical', 'ahl_al_hadith', 597, 'mutawassit', 'mawduʿat', 0.85),
('ابن الصلاح', 'Ibn al-Ṣalāḥ', 'classical', 'ahl_al_hadith', 643, 'mutawassit', 'ʿulum_hadith', 1.0),
('المنذري', 'al-Mundhirī', 'classical', 'ahl_al_hadith', 656, 'mutawassit', 'targhib', 0.9),
('النووي', 'al-Nawawī', 'classical', 'ahl_al_hadith', 676, 'mutawassit', 'sharh_muslim', 0.95);

-- ────────────────────────────────────────────────────────────────────────────
-- MUTAʾAKHKHIRŪN (700-1000 H)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO hukm_sources (name_ar, name_fr, era, manhaj, death_hijri, tabaqah, specialty, reliability_weight) VALUES
('ابن دقيق العيد', 'Ibn Daqīq al-ʿĪd', 'classical', 'ahl_al_hadith', 702, 'mutaakhkhir', 'ihkam', 0.95),
('المزي', 'al-Mizzī', 'classical', 'ahl_al_hadith', 742, 'mutaakhkhir', 'tahdhib_kamal', 1.0),
('الذهبي', 'al-Dhahabī', 'classical', 'ahl_al_hadith', 748, 'mutaakhkhir', 'mizan_siyar', 1.0),
('ابن تيمية', 'Ibn Taymiyyah', 'classical', 'salafi', 728, 'mutaakhkhir', 'manhaj', 0.9),
('ابن القيم', 'Ibn al-Qayyim', 'classical', 'salafi', 751, 'mutaakhkhir', 'fiqh_hadith', 0.9),
('ابن كثير', 'Ibn Kathīr', 'classical', 'ahl_al_hadith', 774, 'mutaakhkhir', 'tafsir_ikhtisar', 0.9),
('ابن رجب', 'Ibn Rajab al-Ḥanbalī', 'classical', 'salafi', 795, 'mutaakhkhir', 'sharh_ʿilal', 1.0),
('العراقي', 'al-ʿIrāqī', 'classical', 'ahl_al_hadith', 806, 'mutaakhkhir', 'alfiyyah_takhrij', 0.95),
('الهيثمي', 'al-Haythamī', 'classical', 'ahl_al_hadith', 807, 'mutaakhkhir', 'majmaʿ_zawaid', 0.9),
('البوصيري', 'al-Būṣīrī', 'classical', 'ahl_al_hadith', 840, 'mutaakhkhir', 'ithaf_zawaid', 0.85),
('ابن حجر العسقلاني', 'Ibn Ḥajar al-ʿAsqalānī', 'classical', 'ahl_al_hadith', 852, 'mutaakhkhir', 'fath_tahdhib', 1.0),
('السخاوي', 'al-Sakhāwī', 'classical', 'ahl_al_hadith', 902, 'mutaakhkhir', 'fath_mughith', 0.9),
('السيوطي', 'al-Suyūṭī', 'classical', 'ahl_al_hadith', 911, 'mutaakhkhir', 'tadrib_rawi', 0.85);

-- ────────────────────────────────────────────────────────────────────────────
-- CONTEMPORAINS SALAFIS (1200 H → aujourd'hui)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO hukm_sources (name_ar, name_fr, era, manhaj, death_hijri, tabaqah, specialty, reliability_weight) VALUES
('الشوكاني', 'al-Shawkānī', 'contemporary', 'salafi', 1250, 'muʿasir', 'nayl_fath_qadir', 0.9),
('صديق حسن خان', 'Ṣiddīq Ḥasan Khān', 'contemporary', 'salafi', 1307, 'muʿasir', 'hadith', 0.85),
('عبدالرحمن المعلمي', 'ʿAbd al-Raḥmān al-Muʿallimī al-Yamānī', 'contemporary', 'salafi', 1386, 'muʿasir', 'jarh_taʿdil', 1.0),
('أحمد شاكر', 'Aḥmad Shākir', 'contemporary', 'salafi', 1377, 'muʿasir', 'tahqiq_musnad', 0.95),
('محمد ناصر الدين الألباني', 'Muḥammad Nāṣir al-Dīn al-Albānī', 'contemporary', 'salafi', 1420, 'muʿasir', 'takhrij_tashih', 1.0),
('عبدالعزيز بن باز', 'ʿAbd al-ʿAzīz ibn Bāz', 'contemporary', 'salafi', 1420, 'muʿasir', 'fatawa', 0.95),
('محمد بن صالح العثيمين', 'Muḥammad ibn Ṣāliḥ al-ʿUthaymīn', 'contemporary', 'salafi', 1421, 'muʿasir', 'sharh', 0.95),
('مقبل بن هادي الوادعي', 'Muqbil ibn Hādī al-Wādiʿī', 'contemporary', 'salafi', 1422, 'muʿasir', 'sahih_musnad', 0.95),
('حماد الأنصاري', 'Ḥammād al-Anṣārī', 'contemporary', 'salafi', 1418, 'muʿasir', 'hadith', 0.9),
('عبدالمحسن العباد', 'ʿAbd al-Muḥsin al-ʿAbbād', 'contemporary', 'salafi', NULL, 'muʿasir', 'sharh_sunan', 0.9),
('صالح الفوزان', 'Ṣāliḥ al-Fawzān', 'contemporary', 'salafi', NULL, 'muʿasir', 'fatawa', 0.85),
('شعيب الأرناؤوط', 'Shuʿayb al-Arnaʾūṭ', 'contemporary', 'ahl_al_hadith', 1438, 'muʿasir', 'tahqiq_musnad', 0.95),
('عبدالقادر الأرناؤوط', 'ʿAbd al-Qādir al-Arnaʾūṭ', 'contemporary', 'ahl_al_hadith', 1425, 'muʿasir', 'tahqiq', 0.9),
('بكر أبو زيد', 'Bakr Abū Zayd', 'contemporary', 'salafi', 1429, 'muʿasir', 'adab_fiqh', 0.85),
('ربيع المدخلي', 'Rabīʿ al-Madkhalī', 'contemporary', 'salafi', NULL, 'muʿasir', 'manhaj', 0.8),
('عبدالعزيز الراجحي', 'ʿAbd al-ʿAzīz al-Rājiḥī', 'contemporary', 'salafi', NULL, 'muʿasir', 'sharh', 0.85),
('عبدالمحسن العباد البدر', 'ʿAbd al-Muḥsin al-ʿAbbād al-Badr', 'contemporary', 'salafi', NULL, 'muʿasir', 'sharh_abu_dawud', 0.9),
('سعد الحميد', 'Saʿd al-Ḥumayyid', 'contemporary', 'salafi', NULL, 'muʿasir', 'hadith', 0.85),
('حمزة المليباري', 'Ḥamzah al-Malībārī', 'contemporary', 'salafi', NULL, 'muʿasir', 'muwazanah_ʿilal', 0.9),
('طارق عوض الله', 'Ṭāriq ʿAwaḍ Allāh', 'contemporary', 'salafi', NULL, 'muʿasir', 'sharh_ʿilal', 0.85),
('بشار عواد معروف', 'Bashshār ʿAwwād Maʿrūf', 'contemporary', 'ahl_al_hadith', NULL, 'muʿasir', 'tahqiq', 0.9),
('الشريف حاتم العوني', 'al-Sharīf Ḥātim al-ʿAwnī', 'contemporary', 'ahl_al_hadith', NULL, 'muʿasir', 'ʿilal_manhaj', 0.85);

-- ============================================================================
-- STATISTIQUES DU SEED
-- ============================================================================
-- Total : ~80 muḥaddithīn répartis en 4 ṭabaqāt
-- - Mutaqaddimūn (avant 300 H) : 35 imams
-- - Mutawassiṭūn (400-700 H) : 9 imams
-- - Mutaʾakhkhirūn (700-1000 H) : 13 imams
-- - Muʿāṣirūn (1200 H → aujourd'hui) : 23 savants
-- ============================================================================
-- FIN DE LA MIGRATION 003
-- ============================================================================
