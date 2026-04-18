/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v18.4 — data.js
   Rôle    : Données pures — ZÉRO logique, ZÉRO DOM, ZÉRO event
   Contenu : window.SCHOLARS_DB  → 19 plaques Silsilah al-Isnad
             window.VERDICTS_DB  → Glossaire Jarḥ wa Taʿdīl
   Chargement : AVANT app.js dans le <head>
   Sources : binbaz.org.sa · alalbany.net · binothaimeen.net
═══════════════════════════════════════════════════════════════════ */

/* ══════════════════════════════════════════════════════════════
   window.SCHOLARS_DB
   Lignée des 14 siècles — 19 plaques de la Silsilah al-Isnad
   Structure par entrée :
     ar  : Nom en arabe
     d   : Dates (naissance–mort, siècle hégire)
     r   : Rôle dans la préservation de la Sunnah
     o   : Ouvrages majeurs
   Lookup : souple par sous-chaîne (nom.toLowerCase())
══════════════════════════════════════════════════════════════ */
window.SCHOLARS_DB = {

  /* ── COUCHE 1 : AS-SAHĀBA ── */
  'abu bakr': {
    ar: 'أبو بكر الصديق',
    d:  '573–634 (1er s. Hégire)',
    r:  'Premier calife. Le plus proche compagnon du Prophète ﷺ. Premier homme libre à croire.',
    o:  'Compilation du Coran sous son califat'
  },
  'omar': {
    ar: 'عمر بن الخطاب',
    d:  '584–644 (1er s. Hégire)',
    r:  'Al-Fārūq. 2e calife bien guidé. A codifié les fondements de l\'État islamique.',
    o:  'Codification du droit islamique'
  },
  'uthman': {
    ar: 'عثمان بن عفان',
    d:  '576–656 (1er s. Hégire)',
    r:  '3e calife bien guidé. A unifié le Coran en un seul Mushaf canonique.',
    o:  'Unification du Mushaf — le Coran tel que nous le connaissons'
  },
  'ali': {
    ar: 'علي بن أبي طالب',
    d:  '601–661 (1er s. Hégire)',
    r:  '4e calife bien guidé. Cousin et gendre du Prophète ﷺ.',
    o:  'Transmission du fiqh et de l\'aqida prophétique'
  },
  'abu hurayra': {
    ar: 'أبو هريرة',
    d:  'm. 678 (1er s. Hégire)',
    r:  'Plus grand transmetteur de hadiths : 5 374 hadiths. Compagnon dévoué à la mémorisation.',
    o:  'Transmission orale aux Tabi\'în'
  },
  'ibn umar': {
    ar: 'عبدالله بن عمر',
    d:  '614–693 (1er s. Hégire)',
    r:  'Fils de Omar. L\'un des plus fidèles transmetteurs de la Sunnah. Refusait d\'innover.',
    o:  '2 630 hadiths transmis — Sahih Bukhari et Muslim'
  },

  /* ── COUCHE 2 : AT-TĀBI'ĪN ── */
  'ibn sirin': {
    ar: 'محمد بن سيرين',
    d:  '654–729 (2e s. Hégire)',
    r:  'Premier à exiger l\'Isnad. A dit : "Cette science est une religion — regardez de qui vous la prenez."',
    o:  'Règle d\'or de l\'Isnad — fondement du Jarh wa Ta\'dil'
  },
  'al zuhri': {
    ar: 'ابن شهاب الزهري',
    d:  '671–742 (2e s. Hégire)',
    r:  'Imam des Tabi\'în en hadith. Premier à avoir compilé le hadith par ordre de Umar ibn Abd al-Aziz.',
    o:  'Fondateur de la compilation systématique du hadith'
  },

  /* ── COUCHE 3 : FONDATEURS DES MADHAHIB ── */
  'malik': {
    ar: 'مالك بن أنس',
    d:  '711–795 (2e s. Hégire)',
    r:  'Imam Dār al-Hijrah. Fondateur du madhhab Mālikite. Disait : "Tout le monde peut être réfuté sauf le Prophète ﷺ."',
    o:  'Al-Muwatta\''
  },
  'shafi': {
    ar: 'الإمام الشافعي',
    d:  '767–820 (2e s. Hégire)',
    r:  'Fondateur de la science des Usul al-Fiqh. A systématisé les règles de dérivation juridique.',
    o:  'Al-Risāla, Al-Umm'
  },
  'ahmad': {
    ar: 'أحمد بن حنبل',
    d:  '780–855 (3e s. Hégire)',
    r:  'Imam Ahl as-Sunnah. A résisté à la Mihna (inquisition mu\'tazilite) sans jamais céder.',
    o:  'Al-Musnad (30 000+ hadiths)'
  },
  'abu hanifa': {
    ar: 'الإمام أبو حنيفة',
    d:  '699–767 (2e s. Hégire)',
    r:  'Fondateur du madhhab Hanafite. Grand faqih de Kufa.',
    o:  'Al-Fiqh al-Akbar'
  },

  /* ── COUCHE 3 : COMPILATEURS ── */
  'bukhari': {
    ar: 'الإمام البخاري',
    d:  '810–870 (3e s. Hégire)',
    r:  'Amīr al-Mu\'minīn fil Hadīth. A sélectionné 7 275 hadiths parmi 600 000 vérifiés.',
    o:  'Sahīh al-Bukhārī'
  },
  'muslim': {
    ar: 'الإمام مسلم',
    d:  '815–875 (3e s. Hégire)',
    r:  'Ḥujjah. 2e recueil le plus authentique. Élève de Bukhari.',
    o:  'Sahīh Muslim'
  },
  'tirmidhi': {
    ar: 'الإمام الترمذي',
    d:  '824–892 (3e s. Hégire)',
    r:  'Imam du hadith. A introduit la classification par grades dans son Sunan.',
    o:  'Jāmi\' at-Tirmidhī'
  },
  'abu dawud': {
    ar: 'الإمام أبو داود',
    d:  '817–889 (3e s. Hégire)',
    r:  'A examiné 500 000 hadiths pour en extraire 4 800 dans son Sunan.',
    o:  'Sunan Abī Dāwūd'
  },
  'nasai': {
    ar: 'الإمام النسائي',
    d:  '829–915 (3e s. Hégire)',
    r:  'L\'un des compilateurs des Six Livres. Connu pour sa sévérité dans l\'évaluation.',
    o:  'Sunan an-Nasā\'ī'
  },
  'ibn majah': {
    ar: 'الإمام ابن ماجه',
    d:  '824–887 (3e s. Hégire)',
    r:  '6e compilateur des Kutub as-Sitta.',
    o:  'Sunan Ibn Mājah'
  },

  /* ── COUCHE 4 : HUFFADH & PILIERS ── */
  'ibn taymiyyah': {
    ar: 'ابن تيمية',
    d:  '1263–1328 (8e s. Hégire)',
    r:  'Shaykh al-Islam. Défenseur de la voie des Salaf contre les innovations. Emprisonné pour la vérité.',
    o:  'Majmū\' al-Fatāwā (37 vol.), Minhāj as-Sunnah'
  },
  'ibn qayyim': {
    ar: 'ابن القيم الجوزية',
    d:  '1292–1350 (8e s. Hégire)',
    r:  'Élève principal d\'Ibn Taymiyyah. Pédagogue de l\'âme et du cœur.',
    o:  'Zād al-Ma\'ād, Madārij as-Sālikīn, I\'lām al-Muwaqqi\'īn'
  },
  'dhahabi': {
    ar: 'الإمام الذهبي',
    d:  '1274–1348 (8e s. Hégire)',
    r:  'Al-Hafiz. Maître de la biographie critique des transmetteurs (Rijal).',
    o:  'Siyar A\'lām an-Nubalā\', Mīzān al-I\'tidāl, Tārikhul Islām'
  },
  'ibn hajar': {
    ar: 'الحافظ ابن حجر العسقلاني',
    d:  '1372–1449 (9e s. Hégire)',
    r:  'Al-Hafiz al-Kabir. Commentateur du Sahih Bukhari. Auteur du manuel de Rijal de référence.',
    o:  'Fath al-Bārī (13 vol.), Taqrīb at-Tahdhīb'
  },
  'nawawi': {
    ar: 'الإمام النووي',
    d:  '1233–1277 (7e s. Hégire)',
    r:  'Grand juriste hanbalite. Commentateur du Sahih Muslim.',
    o:  'Sharh Sahīh Muslim, Riyādh as-Sālihīn, Al-Arba\'ūn an-Nawawiyyah'
  },
  'ibn kathir': {
    ar: 'الحافظ ابن كثير',
    d:  '1301–1373 (8e s. Hégire)',
    r:  'Hafiz et historien. Élève d\'Ibn Taymiyyah. Tafsir de référence mondiale.',
    o:  'Tafsīr al-Qur\'ān al-\'Azīm, Al-Bidāyah wan-Nihāyah'
  },

  /* ── COUCHE 5 : KIBĀR CONTEMPORAINS ── */
  'albani': {
    ar: 'الشيخ الألباني',
    d:  '1914–1999 (15e s. Hégire)',
    r:  'Muhaddith de l\'ère moderne. A vérifié des dizaines de milliers de hadiths. Tazkiya unanime de tous les Kibār.',
    o:  'Silsilat As-Sahīhah, Silsilat Ad-Da\'īfah, Irwā\' al-Ghalīl'
  },
  'ibn baz': {
    ar: 'الشيخ ابن باز',
    d:  '1912–1999 (15e s. Hégire)',
    r:  'Grand Mufti d\'Arabie Saoudite. Référence de toute la Oummah. Aveugle de naissance, hafiz du Coran.',
    o:  'Majmū\' Fatāwā Ibn Bāz (30 vol.)'
  },
  'uthaymin': {
    ar: 'الشيخ ابن عثيمين',
    d:  '1929–2001 (15e s. Hégire)',
    r:  'Grand savant du Najd. Pédagogue hors pair. Membre du Conseil des Grands Savants.',
    o:  'Al-Sharh al-Mumti\' (15 vol.), Sharh Riyādh as-Sālihīn'
  },
  'muqbil': {
    ar: 'مقبل بن هادي الوادعي',
    d:  '1933–2001 (15e s. Hégire)',
    r:  'Imam du Yémen. A fondé l\'école de Dammaj. Porteur de la Da\'wah Salafie au Yémen.',
    o:  'Tarājum Rijāl, Réfutations'
  },
  'rabi': {
    ar: 'الشيخ ربيع المدخلي',
    d:  'Né en 1931 (15e s. Hégire)',
    r:  'Porteur du Jarḥ wa Taʿdīl contemporain. Recommandé par Al-Albani, Ibn Baz et Ibn Uthaymin.',
    o:  'Al-\'Awāsim, Bayānu Fasād Mi\'yār, Manhaj al-Anbiyā\''
  },
  'fawzan': {
    ar: 'الشيخ صالح الفوزان',
    d:  'Né en 1933 (15e s. Hégire)',
    r:  'Membre du Conseil des Grands Savants. Référence en aqida et fiqh contemporain.',
    o:  'Al-Mulakhkhas al-Fiqhī, I\'ānat al-Mustafīd'
  },
  'madkhali': {
    ar: 'الشيخ ربيع المدخلي',
    d:  'Né en 1931 (15e s. Hégire)',
    r:  'Porteur du Jarḥ wa Taʿdīl contemporain. Recommandé par Al-Albani, Ibn Baz et Ibn Uthaymin.',
    o:  'Al-\'Awāsim, Bayānu Fasād Mi\'yār, Manhaj al-Anbiyā\''
  }

};

/* ══════════════════════════════════════════════════════════════
   window.VERDICTS_DB
   Glossaire Jarḥ wa Taʿdīl — Dictionnaire des 14 siècles
   Clé    : terme en minuscules (correspondance souple)
   Valeur : traduction française + explication méthodologique
   Source : Taqrīb at-Tahdhīb (Ibn Ḥajar) · Sharḥ ʿIlal
            at-Tirmidhī · Lisān al-Mīzān (Ibn Ḥajar)
══════════════════════════════════════════════════════════════ */
window.VERDICTS_DB = {

  /* ── TADIL — Recommandations (du plus fort au plus faible) ── */
  'thiqah thabt':       'Confiance absolue + mémoire parfaite — Le summum du Tadil',
  'thiqah thiqa':       'Confiance absolue + mémoire parfaite — Redoublement pour insister',
  'thiqah':             'Digne de confiance — Niveau fondamental du Tadil',
  'thabt':              'Mémoire parfaite et fixe — Qualité de précision maximale',
  'hujjah':             'Autorité faisant preuve — Hadith retenu comme preuve',
  'hafiz':              'Mémorisateur de 100 000 hadiths minimum avec leurs isnad',
  'muhaddith':          'Savant spécialiste des sciences du hadith et de ses transmetteurs',
  'imam':               'Imam de la Sunnah — Référence pour sa génération',
  'adul par ijma':      'Juste par consensus unanime des savants — Les Sahaba',
  'saduq':              'Véridique — Transmetteur fiable mais niveau inférieur à Thiqah',
  'saduq yaham':        'Véridique mais commet parfois des erreurs d\'inattention',
  'maqbul':             'Acceptable — Hadith retenu si corroboré (Mutaba\'at)',
  'muhaddith al asr':   'Muhaddith de l\'ère moderne — Titre d\'Al-Albani selon les Kibār',
  'shaykh al islam':    'Le plus grand savant de son époque — Titre d\'Ibn Taymiyyah',
  'amir al muminin':    'Prince des croyants en hadith — Titre d\'Al-Bukhari',
  'hujjat al islam':    'Preuve de l\'Islam en science du hadith',

  /* ── JARH — Critiques (du plus léger au plus sévère) ── */
  'layyin':             'Légèrement affaibli — Hadith pris avec précaution',
  'fihi layyin':        'Il y a une légère faiblesse en lui — prudence requise',
  'da if':              'Faible — Hadith non retenu comme preuve indépendante',
  'daif':               'Faible — Hadith non retenu comme preuve indépendante',
  'fihi kalaam':        'Il est critiqué — affaiblissement documenté',
  'matruk':             'Abandonné — Hadith rejeté par les savants du Rijal',
  'munkar':             'Réprouvé — Contredit les transmetteurs fiables',
  'majhul':             'Inconnu — Identité ou fiabilité non établie',
  'majhul hal':         'Situation inconnue — Mentionné mais non évalué',
  'mudallis':           'Pratique la dissimulation (Tadlis) dans l\'Isnad',
  'kathir al khata':    'Commet de nombreuses erreurs dans la transmission',
  'kadhdhab':           'Menteur délibéré — Hadith absolument rejeté',
  'wadd al hadith':     'Fabricateur de hadiths — Le pire degré du Jarh',
  'mawdu':              'Inventé — Forgé délibérément, attribué faussement au Prophète ﷺ',
  'munqati':            'Chaîne brisée — Un ou plusieurs transmetteurs manquants',
  'mursal':             'Hadith rapporté par un Tabi\'î sans mentionner le Sahabi',
  'mu dal':             'Deux transmetteurs ou plus manquants dans la chaîne',
  'mudtarib':           'Hadith contradictoire — Transmis de façons incompatibles',
  'shadh':              'Isolé — Contredit par un transmetteur plus fiable',
  'muallaq':            'Suspendu — Début de chaîne supprimé par le compilateur',

  /* ── VERDICTS GLOBAUX ── */
  'sahih':              'Authentique — Les 5 conditions de l\'Isnad sont réunies',
  'hasan':              'Bon — Légèrement inférieur au Sahih mais retenu comme preuve',
  'hasan sahih':        'Bon et authentique — Bukhari et Muslim l\'ont tous deux retenu',
  'da if jiddan':       'Très faible — Ne peut servir de preuve même en appoint',
  'batil':              'Nul et non avenu — Sans fondement dans aucune chaîne valide',
  'la asla lahu':       'Sans aucun fondement — N\'a jamais existé dans la tradition',
  'maudu':              'Inventé — Forgé délibérément, attribué faussement au Prophète ﷺ'

};

/* ══════════════════════════════════════════════════════════════
   Confirmation de chargement
══════════════════════════════════════════════════════════════ */
console.log('%c ✅ Mîzân v18.4 — data.js : SCHOLARS_DB (' + Object.keys(window.SCHOLARS_DB).length + ' entrées) + VERDICTS_DB (' + Object.keys(window.VERDICTS_DB).length + ' termes) chargés', 'color:#d4af37;font-weight:bold;');
