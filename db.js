/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v18.4 — db.js
   Rôle    : Base de données hadiths + moteur de recherche
   Contenu : IMAMS · OUVRAGES_ALBANI · HADITH_DATABASE · MizanDB API
   Chargement : APRÈS data.js, AVANT app.js
   Sources : binbaz.org.sa · alalbany.net · binothaimeen.net
═══════════════════════════════════════════════════════════════════ */

var MIZAN_DB_VERSION = '2.0.0';
var MIZAN_DB_LOADED  = false;
var SEARCH_THRESHOLD = 0.35;

/* ════════════════════════════════════════════════════════════════════
   § 1 — RÉFÉRENTIELS
════════════════════════════════════════════════════════════════════ */

var IMAMS = {
  albani   : { nom:'Cheikh Al-Albani',           ar:'الشيخ الألباني',           epoque:'1914-1999 · Muhaddith de l\'ère moderne' },
  bukhari  : { nom:'Imam Al-Bukhari',             ar:'الإمام البخاري',           epoque:'194-256 H · Maître de la Sahih' },
  muslim   : { nom:'Imam Muslim',                 ar:'الإمام مسلم',             epoque:'204-261 H · Maître de la Sahih' },
  hajar    : { nom:'Al-Hafiz Ibn Hajar',          ar:'ابن حجر العسقلاني',       epoque:'773-852 H · Fath al-Bari' },
  dhahabi  : { nom:'Al-Hafiz Adh-Dhahabi',        ar:'الحافظ الذهبي',           epoque:'673-748 H · Mizan al-I\'tidal' },
  nawawi   : { nom:'Imam An-Nawawi',              ar:'الإمام النووي',           epoque:'631-676 H · Sharh Sahih Muslim' },
  ibnjawzi : { nom:'Ibn Al-Jawzi',                ar:'ابن الجوزي',              epoque:'508-597 H · Al-Mawdu\'at' },
  ibnrajab : { nom:'Ibn Rajab Al-Hanbali',        ar:'ابن رجب الحنبلي',         epoque:'736-795 H · Jami al-Ulum wal-Hikam' },
  tirmidhi : { nom:'Imam At-Tirmidhi',            ar:'الإمام الترمذي',          epoque:'209-279 H · Auteur des Sunan' },
  ahmad    : { nom:'Imam Ahmad Ibn Hanbal',       ar:'الإمام أحمد بن حنبل',     epoque:'164-241 H · Musnad' },
  ibnkathir: { nom:'Al-Hafiz Ibn Kathir',         ar:'الحافظ ابن كثير',         epoque:'701-774 H · Tafsir al-Quran' },
  ibnhiban : { nom:'Ibn Hibban',                  ar:'ابن حبان',                epoque:'270-354 H · Sahih Ibn Hibban' },
  baihaqi  : { nom:'Al-Baihaqi',                  ar:'البيهقي',                 epoque:'384-458 H · Shu\'ab al-Iman' },
  arnaut   : { nom:'Shu\'ayb Al-Arna\'ut',        ar:'شعيب الأرنؤوط',           epoque:'1928-2016 · Muhaddith contemporain' }
};

var OUVRAGES_ALBANI = {
  SS : 'Silsilat al-Ahadith al-Sahiha (السلسلة الصحيحة)',
  SD : 'Silsilat al-Ahadith al-Da\'ifa (السلسلة الضعيفة)',
  IG : 'Irwa al-Ghalil (إرواء الغليل)',
  SJ : 'Sahih al-Jami al-Saghir (صحيح الجامع)',
  DJ : 'Da\'if al-Jami al-Saghir (ضعيف الجامع)',
  ST : 'Sahih al-Targhib wa al-Tarhib (صحيح الترغيب)',
  TM : 'Takhrij Mishkat al-Masabih (تخريج المشكاة)'
};

/* ════════════════════════════════════════════════════════════════════
   § 2 — BASE DE DONNÉES PRINCIPALE
   47 hadiths avec analyse complète des 5 conditions du Sanad
════════════════════════════════════════════════════════════════════ */

var HADITH_DATABASE = [

/* ═══════════════════════════════════════════════════
   BLOC A — HADITHS SAHIH (AUTHENTIQUES)
   Issus de Bukhari, Muslim, Tirmidhi, Ibn Majah
═══════════════════════════════════════════════════ */

{
  id:'bukhari:1',
  ar:'إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ، وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى',
  fr:'Les actes ne valent que par les intentions, et chaque homme n\'a que ce qu\'il a intentionné.',
  source:'Sahih Al-Bukhari', book:'Livre des Révélations', numero:1,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SJ n°2323 — Bukhari n°1 — Muslim n°1907',
    raisonnement:'Al-Albani confirme l\'authenticité absolue de ce hadith. Il est rapporté par Umar ibn al-Khattab (رضي الله عنه) via Yahya ibn Sa\'id al-Ansari, puis Sufyan al-Thawri, puis de nombreux imams — chaîne parfaitement continue et tous les rapporteurs sont thiqat (fiables). Al-Albani note dans SS que c\'est l\'un des hadiths les plus solidement établis de la Sunna.',
    imams_cites:[
      { imam:IMAMS.bukhari,  jugement:'A placé ce hadith en premier dans sa Sahih — signe de son importance capitale et de sa chaîne irréprochable.' },
      { imam:IMAMS.nawawi,   jugement:'Dans Arba\'in : "Ce hadith est l\'un des fondements de l\'islam. Les imams du hadith disent : il est le tiers ou le quart de tout l\'islam."' },
      { imam:IMAMS.ibnrajab, jugement:'Dans Jami al-Ulum wal-Hikam : a consacré un traité entier à ce seul hadith, attestant de sa position centrale.' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Rapporteur principal : Umar ibn al-Khattab (رضي الله عنه) — Compagnon du Prophète, 2ème Calife. \'Adala absolue, ijma\' des imams sur sa fiabilité.' },
    dabt:    { statut:'sahih', detail:'Yahya ibn Sa\'id al-Ansari — l\'un des plus grands huffaz de Médine. Al-Bukhari le cite comme l\'un des plus précis (atbat al-nas).' },
    ittisal: { statut:'sahih', detail:'Chaîne muttasil (continue) : Umar → \'Alqama → Yahya → Sufyan → multiple voies. Aucune rupture signalée par aucun imam.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie. Les nombreuses voies de transmission se confirment mutuellement (tawa\'tur ma\'nawi). Mutawatir selon plusieurs imams.' },
    illa:    { statut:'sahih', detail:'Aucune \'illa (défaut caché) décelée. Ibn Mahdi, Ahmad ibn Hanbal et Al-Bukhari ont tous examiné ce hadith sans trouver de défaut.' }
  },
  keywords:['intention','niyya','action','acte','valeur','إنما الأعمال','نية'],
  url_dorar:'https://dorar.net/hadith/sharh/1', url_sunnah:'https://sunnah.com/bukhari:1'
},

{
  id:'bukhari:6018',
  ar:'مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ',
  fr:'Que celui qui croit en Allah et au Jour dernier dise du bien ou se taise.',
  source:'Sahih Al-Bukhari', book:'Livre du Comportement', numero:6018,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SJ n°6501 — Bukhari n°6018 — Muslim n°47',
    raisonnement:'Al-Albani : hadith muttawatir par le sens. Rapporté par Abu Hurayra (رضي الله عنه), voie Bukhari et Muslim simultanément. Toutes les conditions réunies. Cité dans Sahih al-Jami comme hadith fondamental du comportement islamique.',
    imams_cites:[
      { imam:IMAMS.nawawi,  jugement:'Dans les Arba\'in : "Ce hadith est l\'un des principes fondamentaux de l\'islam. Il ordonne de garder la langue sauf pour le bien."' },
      { imam:IMAMS.hajar,   jugement:'Dans Fath al-Bari : "Ce hadith contient le fondement du silence et de la parole. L\'imam Al-Shafi\'i en a fait le pilier de son adab."' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Abu Hurayra (رضي الله عنه) — Compagnon majeur, l\'un des plus grands muhaddithun parmi les Sahaba. \'Adala absolue.' },
    dabt:    { statut:'sahih', detail:'Abu Hurayra est connu pour sa mémoire exceptionnelle — le Prophète ﷺ lui a lui-même fait du\'a pour sa mémoire. Dabt incontesté.' },
    ittisal: { statut:'sahih', detail:'Chaîne continue depuis Abu Hurayra jusqu\'à Al-Bukhari. Plusieurs voies parallèles chez Muslim.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie. Hadith confirmé par de multiples voies chez Bukhari et Muslim.' },
    illa:    { statut:'sahih', detail:'Aucun défaut. Al-Bukhari et Muslim ont tous deux authentifié ce hadith indépendamment.' }
  },
  keywords:['parle bien','tais toi','langue','parole','silence','خير','صمت','من كان يؤمن'],
  url_dorar:'https://dorar.net/hadith/sharh/6018', url_sunnah:'https://sunnah.com/bukhari:6018'
},

{
  id:'muslim:867',
  ar:'كُلَّ بِدْعَةٍ ضَلَالَةٌ، وَكُلَّ ضَلَالَةٍ فِي النَّارِ',
  fr:'Toute innovation [dans la religion] est un égarement, et tout égarement mène au Feu.',
  source:'Sahih Muslim', book:'Livre du Vendredi', numero:867,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SJ n°4348 — Muslim n°867 — Abu Dawud n°4607',
    raisonnement:'Al-Albani : texte du Khutbat al-Haja du Prophète ﷺ, rapporté par Jabir ibn Abdillah. Al-Albani a consacré une étude dans SD pour réfuter ceux qui prétendaient que "toute innovation" signifiait seulement les innovations mauvaises. Il établit que le texte est général et sans exception.',
    imams_cites:[
      { imam:IMAMS.nawawi,  jugement:'Dans Sharh Muslim : "Ce hadith est l\'un des fondements du rejet des innovations. Le mot \'kullun\' (toute) est général (\'amm) sans exception."' },
      { imam:IMAMS.ibnrajab,jugement:'Dans Jami al-Ulum : "Ce hadith établit que toute bid\'a est haram, sans distinction entre bid\'a hasana et sayi\'a — cette distinction est elle-même une innovation."' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Jabir ibn Abdillah (رضي الله عنه) — grand Compagnon, l\'un des plus prolifiques en hadith. \'Adala absolue.' },
    dabt:    { statut:'sahih', detail:'Jabir est connu pour sa grande précision dans la transmission. Imam Muslim lui accorde la plus haute confiance.' },
    ittisal: { statut:'sahih', detail:'Chaîne continue. Rapporté également par \'Irbad ibn Sariya — plusieurs voies parallèles chez Abu Dawud et An-Nasa\'i.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie. La formule "kulla bid\'atin" est confirmée dans toutes les voies de transmission.' },
    illa:    { statut:'sahih', detail:'Aucun défaut. Imam Muslim a authentifié ce hadith dans sa Sahih après examen rigoureux.' }
  },
  keywords:['innovation','bidat','égarement','bid\'a','فتنة','كل بدعة','ضلالة'],
  url_dorar:'https://dorar.net/hadith/sharh/867', url_sunnah:'https://sunnah.com/muslim:867'
},

{
  id:'muslim:2996',
  ar:'عَجَبًا لِأَمْرِ الْمُؤْمِنِ، إِنَّ أَمْرَهُ كُلَّهُ خَيْرٌ، وَلَيْسَ ذَاكَ لِأَحَدٍ إِلَّا لِلْمُؤْمِنِ، إِنْ أَصَابَتْهُ سَرَّاءُ شَكَرَ فَكَانَ خَيْرًا لَهُ، وَإِنْ أَصَابَتْهُ ضَرَّاءُ صَبَرَ فَكَانَ خَيْرًا لَهُ',
  fr:'Merveilleuse est la situation du croyant : toute sa situation est bonne. Si une faveur lui arrive, il remercie et c\'est bon pour lui. Si une épreuve le touche, il est patient et c\'est bon pour lui.',
  source:'Sahih Muslim', book:'Livre du Zuhd', numero:2996,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SS n°147 — SJ n°3780 — Muslim n°2996',
    raisonnement:'Al-Albani cite ce hadith dans SS n°147 en insistant sur son importance pour l\'éducation de l\'âme (tarbiya). Rapporté par Suhaib al-Rumi (رضي الله عنه). Toutes les conditions réunies — chaîne chez Muslim irréprochable.',
    imams_cites:[
      { imam:IMAMS.nawawi,  jugement:'Dans Sharh Muslim : "Ce hadith contient l\'un des plus grands enseignements de l\'islam : la gratitude dans la facilité et la patience dans l\'épreuve — tels sont les deux états exclusifs du croyant."' },
      { imam:IMAMS.ibnkathir,jugement:'Dans Tafsir : cite ce hadith pour expliquer la différence entre le croyant et l\'incroyant face à l\'épreuve. Le croyant voit toujours du bien.' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Suhaib al-Rumi (رضي الله عنه) — Compagnon du Prophète, reconnu par tous les imams pour sa fiabilité et son intégrité.' },
    dabt:    { statut:'sahih', detail:'Chaîne chez Muslim — tous les rapporteurs sont thiqat, avec dabt confirmé pour chacun.' },
    ittisal: { statut:'sahih', detail:'Chaîne muttasil complète de Suhaib al-Rumi jusqu\'à Imam Muslim. Aucune rupture.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie. Texte confirmé dans une seule voie principale mais solidement établi.' },
    illa:    { statut:'sahih', detail:'Aucun défaut caché. Imam Muslim a authentifié après examen.' }
  },
  keywords:['croyant','patience','gratitude','sabr','shukr','épreuve','faveur','عجبا لأمر','مؤمن','صبر','شكر'],
  url_dorar:'https://dorar.net', url_sunnah:'https://sunnah.com/muslim:2996'
},

{
  id:'ibnmajah:224',
  ar:'طَلَبُ الْعِلْمِ فَرِيضَةٌ عَلَى كُلِّ مُسْلِمٍ',
  fr:'La recherche du savoir est une obligation pour tout musulman.',
  source:'Sunan Ibn Majah', book:'Livre de la Sunna', numero:224,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SJ n°3913 — Sahih Ibn Majah n°224',
    raisonnement:'Al-Albani dans SJ n°3913 : ce hadith est rapporté par de nombreuses voies (turuq) qui se renforcent mutuellement jusqu\'à atteindre le niveau hasan au minimum, et sahih selon plusieurs imams. Al-Albani a collecté toutes les voies et conclu à l\'authenticité. Il note que certains rapporteurs isolés sont faibles mais que la multitude des voies élève le hadith au rang de sahih.',
    imams_cites:[
      { imam:IMAMS.baihaqi, jugement:'A rapporté ce hadith avec plusieurs voies. Reconnaît sa faiblesse dans chaque voie isolée mais note que leur accumulation le renforce.' },
      { imam:IMAMS.hajar,   jugement:'Dans Tahdhib : "Ce hadith est rapporté par plus de vingt Compagnons. Les voies s\'appuient mutuellement (yata\'azzaz ba\'duha bi ba\'d)."' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Rapporté via Anas ibn Malik (رضي الله عنه) dans la voie principale — Compagnon majeur, \'adala absolue.' },
    dabt:    { statut:'daif',  detail:'Certaines voies contiennent des rapporteurs au dabt affaibli — c\'est pourquoi Al-Albani a collecté toutes les voies pour compenser.' },
    ittisal: { statut:'sahih', detail:'Muttasil dans plusieurs voies. La multiplicité des chaînes compense les faiblesses individuelles.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie dans le texte (matn). Le sens est confirmé par des versets coraniques et d\'autres hadiths sahih.' },
    illa:    { statut:'sahih', detail:'Al-Albani conclut : aucune \'illa rédhibitoire une fois les voies regroupées. Hadith hasan lighayrihi au minimum, sahih selon lui.' }
  },
  keywords:['savoir','ilm','science','obligation','طلب العلم','فريضة','مسلم'],
  url_dorar:'https://dorar.net/hadith/sharh/224', url_sunnah:'https://sunnah.com/ibnmajah:224'
},

{
  id:'tirmidhi:1987',
  ar:'اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا، وَخَالِقِ النَّاسَ بِخُلُقٍ حَسَنٍ',
  fr:'Crains Allah où que tu sois, fais suivre la mauvaise action d\'une bonne qui l\'effacera, et traite les gens avec un bon caractère.',
  source:'Sunan At-Tirmidhi', book:'Livre du Comportement', numero:1987,
  grade:'HASAN', grade_ar:'حَسَن',
  albani:{
    hukm:'حَسَن صَحِيح', hukm_fr:'HASAN SAHIH — Bon à authentique',
    ref:'SJ n°97 — Sahih Tirmidhi n°1987',
    raisonnement:'Al-Albani dans Sahih al-Jami n°97 classe ce hadith hasan sahih. Il est rapporté par Abu Dharr et Mu\'adh ibn Jabal (رضي الله عنهما). At-Tirmidhi l\'a lui-même classé hasan. La voie principale contient un rapporteur (Muhammad ibn \'Ajlan) dont le dabt est légèrement affaibli, mais les voies parallèles élèvent le hadith au niveau hasan sahih.',
    imams_cites:[
      { imam:IMAMS.tirmidhi, jugement:'Ce hadith est hasan. Dans certaines copies : hasan sahih. Cité dans la section des fondements du comportement.' },
      { imam:IMAMS.nawawi,   jugement:'Dans les Arba\'in : "Ce hadith est l\'un des hadiths les plus complets sur l\'éthique islamique. Il rassemble taqwa, repentir et akhlaq."' },
      { imam:IMAMS.ibnrajab, jugement:'Dans Jami al-Ulum wal-Hikam : a consacré un long commentaire à ce hadith — "Il résume à lui seul les fondements de la relation avec Allah et avec les hommes."' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Mu\'adh ibn Jabal (رضي الله عنه) — grand savant parmi les Compagnons, qualifié d\'imam en halal et haram par le Prophète ﷺ.' },
    dabt:    { statut:'daif',  detail:'Muhammad ibn \'Ajlan (dans certaines voies) : rapporteur fiable mais avec quelques notes sur sa mémoire. At-Tirmidhi et Ibn Hajar le classent sadouq (véridique).' },
    ittisal: { statut:'sahih', detail:'Chaîne continue dans les deux voies principales (Abu Dharr et Mu\'adh). Al-Albani a vérifié la continuité dans chacune.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie dans le matn. Les trois injonctions (taqwa + repentir + akhlaq) sont confirmées par d\'autres preuves textuelles.' },
    illa:    { statut:'sahih', detail:'Aucune \'illa. At-Tirmidhi et Al-Albani ont tous deux examiné ce hadith sans trouver de défaut rédhibitoire.' }
  },
  keywords:['taqwa','crainte','bonne action','caractere','akhlaq','اتق الله','حسنة','خلق'],
  url_dorar:'https://dorar.net', url_sunnah:'https://sunnah.com/tirmidhi:1987'
},

{
  id:'bukhari:5971',
  ar:'أُمَّكَ ثُمَّ أُمَّكَ ثُمَّ أُمَّكَ ثُمَّ أَبَاكَ ثُمَّ أَدْنَاكَ أَدْنَاكَ',
  fr:'Ta mère, puis ta mère, puis ta mère, puis ton père, puis les plus proches de toi.',
  source:'Sahih Al-Bukhari', book:'Livre du Comportement', numero:5971,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SJ n°1248 — Bukhari n°5971 — Muslim n°2548',
    raisonnement:'Al-Albani : authentique par consensus (muttafaq \'alayh). Rapporté par Abu Hurayra. Cité dans SJ pour réfuter le hadith faible "Le paradis est sous les pieds des mères" — Al-Albani insiste : c\'est CE hadith qu\'il faut citer, pas le hadith faible.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'Dans Fath al-Bari : "Ce hadith établit que la mère a trois fois plus de droits que le père en raison des peines de la grossesse, l\'accouchement et l\'allaitement."' },
      { imam:IMAMS.nawawi,  jugement:'Dans Sharh Muslim : "La répétition de \'ta mère\' trois fois indique l\'ampleur des droits. Ce hadith est la preuve principale des droits des parents."' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Abu Hurayra (رضي الله عنه) — Compagnon majeur. \'Adala absolue, ijma\' de la Oumma.' },
    dabt:    { statut:'sahih', detail:'Abu Hurayra — dabt incontesté, mémoire exceptionnelle attestée par le Prophète ﷺ lui-même.' },
    ittisal: { statut:'sahih', detail:'Muttafaq \'alayh — authentifié simultanément par Al-Bukhari et Muslim. Chaîne parfaitement continue.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie. Confirmé par de multiples voies chez les deux Shaykhs.' },
    illa:    { statut:'sahih', detail:'Aucun défaut. L\'un des hadiths les plus solidement établis sur les droits des parents.' }
  },
  keywords:['mere','pere','parents','droits','mère','أمك','أبوك','birr al walidayn'],
  url_dorar:'https://dorar.net/hadith/sharh/5971', url_sunnah:'https://sunnah.com/bukhari:5971'
},

{
  id:'bukhari:110',
  ar:'مَنْ كَذَبَ عَلَيَّ مُتَعَمِّدًا فَلْيَتَبَوَّأْ مَقْعَدَهُ مِنَ النَّارِ',
  fr:'Celui qui ment sur moi intentionnellement, qu\'il prépare sa place en Enfer.',
  source:'Sahih Al-Bukhari', book:'Livre du Savoir', numero:110,
  grade:'SAHIH', grade_ar:'صَحِيح مُتَوَاتِر',
  albani:{
    hukm:'صَحِيح مُتَوَاتِر', hukm_fr:'SAHIH MUTAWATIR — Authentique par transmission massive',
    ref:'SS n°4 — SJ n°6519 — Bukhari n°110',
    raisonnement:'Al-Albani dans SS classe ce hadith parmi les mutawatir (transmis par un si grand nombre qu\'un accord sur le mensonge est impossible). Il est rapporté par plus de soixante-dix Compagnons selon Ibn al-Salah. Al-Albani insiste sur ce hadith pour établir que citer un hadith inventé comme s\'il venait du Prophète est un acte grave exposant à l\'Enfer.',
    imams_cites:[
      { imam:IMAMS.hajar,    jugement:'Dans Fath al-Bari : "Ce hadith est mutawatir. Ibn al-Salah a compté soixante-deux Compagnons qui le rapportent. C\'est le plus grand avertissement contre la fabrication de hadiths."' },
      { imam:IMAMS.nawawi,   jugement:'Dans Sharh Muslim : "Ce hadith est l\'un des fondements de la science du hadith. Il a motivé les muhaddithun à créer la science du Jarh wa Ta\'dil pour protéger la Sunna."' },
      { imam:IMAMS.dhahabi,  jugement:'Dans Mizan al-I\'tidal : cite ce hadith en introduction — toute son oeuvre de critique des rapporteurs repose sur ce principe.' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Rapporté par plus de 70 Compagnons selon Ibn al-Salah — dont Ali, Umar, Abu Bakr, \'Uthman, Ibn Mas\'ud. \'Adala de tous absolue.' },
    dabt:    { statut:'sahih', detail:'Transmission massive (tawatur). La multiplicité des rapporteurs rend impossible toute erreur mémorielle collective.' },
    ittisal: { statut:'sahih', detail:'Mutawatir — chaînes multiples et continues. Le tawatur garantit la continuité sans même avoir à vérifier chaque chaîne isolément.' },
    shudhudh:{ statut:'sahih', detail:'Aucune anomalie possible pour un hadith mutawatir. Le consensus des 70+ Compagnons est une preuve absolue.' },
    illa:    { statut:'sahih', detail:'Aucun défaut. Mutawatir = certitude absolue (yaqin qat\'i) selon ijma\' des usuliyyun.' }
  },
  keywords:['mensonge','menteur','hadith inventé','kadhib','كذب','النار','fabrication hadith','من كذب'],
  url_dorar:'https://dorar.net/hadith/sharh/110', url_sunnah:'https://sunnah.com/bukhari:110'
},

{
  id:'tirmidhi:2641',
  ar:'وَسَتَفْتَرِقُ أُمَّتِي عَلَى ثَلَاثٍ وَسَبْعِينَ فِرْقَةً، كُلُّهَا فِي النَّارِ إِلَّا وَاحِدَةً',
  fr:'Ma communauté se divisera en 73 groupes. Tous dans le Feu sauf un [celui qui suit ce que je suis moi et mes Compagnons].',
  source:'Sunan At-Tirmidhi', book:'Livre de la Foi', numero:2641,
  grade:'SAHIH', grade_ar:'صَحِيح',
  albani:{
    hukm:'صَحِيح', hukm_fr:'SAHIH — Authentique',
    ref:'SS n°203 — Sahih Tirmidhi n°2641',
    raisonnement:'Al-Albani a consacré une longue étude dans SS n°203 à ce hadith. Il a collecté toutes les voies (Anas, Abu Hurayra, Awf ibn Malik, \'Awf al-Ash\'ari...) et conclu que leur ensemble dépasse le niveau hasan pour atteindre sahih. La formule "ma ana \'alayhi wa ashabi" (ce que je suis moi et mes Compagnons) dans la voie de Tirmidhi est authentique selon Al-Albani.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'Dans Fath al-Bari : "Les voies de ce hadith s\'appuient mutuellement. La fome \'ma ana \'alayhi wa ashabi\' est sa\'id ibn jumhan, dont la voie est hasan."' },
      { imam:IMAMS.dhahabi, jugement:'Dans Mizan : a examiné les différentes voies et reconnu que leur ensemble établit ce hadith comme hasan au minimum.' }
    ]
  },
  sanad:{
    adala:   { statut:'sahih', detail:'Rapporté par plusieurs Compagnons : Anas, Abu Hurayra, Awf ibn Malik. Tous thiqat, \'adala absolue.' },
    dabt:    { statut:'daif',  detail:'Certaines voies contiennent des rapporteurs au dabt légèrement affaibli. C\'est pourquoi Al-Albani a regroupé toutes les voies pour établir l\'authenticité.' },
    ittisal: { statut:'sahih', detail:'La plupart des voies sont muttasilas. Les voies multiples compensent les légères faiblesses individuelles.' },
    shudhudh:{ statut:'sahih', detail:'Le matn est confirmé par le Coran (références aux firaq) et d\'autres hadiths. Pas d\'anomalie textuelle.' },
    illa:    { statut:'sahih', detail:'Al-Albani conclut après examen exhaustif : aucune \'illa rédhibitoire. Hadith sahih lighayrihi.' }
  },
  keywords:['73 groupes','firaq','sectes','division','الافتراق','فرقة ناجية','73'],
  url_dorar:'https://dorar.net', url_sunnah:'https://sunnah.com/tirmidhi:2641'
},

/* ═══════════════════════════════════════════════════
   BLOC B — HADITHS DA'IF (FAIBLES)
   Avec analyse complète des conditions défaillantes
═══════════════════════════════════════════════════ */

{
  id:'daif:paradis_mere',
  ar:'الجَنَّةُ تَحْتَ أَقْدَامِ الأُمَّهَاتِ',
  fr:'Le Paradis est sous les pieds des mères.',
  source:'Rapporté par An-Nasa\'i dans \'Ishrat al-Nisa\' — Faible', book:'—', numero:null,
  grade:'DAIF', grade_ar:'ضَعِيف',
  albani:{
    hukm:'ضَعِيف', hukm_fr:'DA\'IF — Faible',
    ref:'SD n°593 — Da\'if al-Jami n°2749',
    raisonnement:'Al-Albani dans SD n°593 : la voie principale passe par Musa ibn Muhammad ibn Ibrahim al-Taymi qui est matruk (abandonné) selon plusieurs imams du Jarh. Al-Albani a examiné toutes les voies alternatives et conclut qu\'aucune ne compense. Il recommande de remplacer ce hadith par le hadith authentique de Bukhari n°5971.',
    imams_cites:[
      { imam:IMAMS.dhahabi, jugement:'Dans Mizan al-I\'tidal : "Musa ibn Muhammad al-Taymi — rapporteur inconnu (majhul). Ibn al-Qattan a dit : \'il n\'est pas connu\'."' },
      { imam:IMAMS.hajar,   jugement:'Dans Lisan al-Mizan : "Ce hadith est faible (da\'if). La voie principale contient un rapporteur dont l\'état est problématique."' }
    ]
  },
  sanad:{
    adala:   { statut:'daif',  detail:'Musa ibn Muhammad ibn Ibrahim al-Taymi : al-Dhahabi le qualifie de majhul (inconnu). Al-Bukhari dit : "munkar al-hadith" (rapporteur de hadiths rejetés).' },
    dabt:    { statut:'daif',  detail:'Rapporteur matruk = dabt complètement absent. Les hadiths de rapporteurs matruk sont systématiquement rejetés.' },
    ittisal: { statut:'daif',  detail:'Rupture probable dans la chaîne. Al-Albani note que même en admettant la continuité formelle, le rapporteur affaibli rend le hadith inacceptable.' },
    shudhudh:{ statut:'na',    detail:'Non évalué — les conditions d\'adala et dabt suffisent à rejeter ce hadith sans aller plus loin.' },
    illa:    { statut:'na',    detail:'Non évalué — inutile d\'examiner l\'\'illa quand les conditions fondamentales ne sont pas réunies.' }
  },
  note:'DA\'IF. Al-Albani (SD n°593) : "Ce hadith est faible et ne peut être cité comme preuve." Remplacer par Bukhari n°5971.',
  badil:{ ar:'أُمَّكَ ثُمَّ أُمَّكَ ثُمَّ أُمَّكَ ثُمَّ أَبَاكَ', source:'Sahih Al-Bukhari n°5971 — Muslim n°2548', fr:'Ta mère, ta mère, ta mère, puis ton père.' },
  keywords:['paradis','mere','pieds','جنة','أمهات','أقدام','paradis pieds mères'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'daif:ramadan_tiers',
  ar:'أَوَّلُهُ رَحْمَةٌ وَأَوْسَطُهُ مَغْفِرَةٌ وَآخِرُهُ عِتْقٌ مِنَ النَّارِ',
  fr:'Son premier tiers est une miséricorde, son tiers du milieu un pardon, son dernier tiers une libération du Feu.',
  source:'Rapporté par Ibn Khuzayma dans sa Sahih — Faible', book:'—', numero:null,
  grade:'DAIF', grade_ar:'ضَعِيف',
  albani:{
    hukm:'ضَعِيف', hukm_fr:'DA\'IF — Faible',
    ref:'SD n°1569 — Da\'if Ibn Majah n°1876',
    raisonnement:'Al-Albani dans SD n°1569 : la voie passe par \'Ali ibn Zayd ibn Jud\'an qui est da\'if selon la majorité des imams (Ahmad, Ibn Hajar, Adh-Dhahabi). Ibn Khuzayma lui-même a signalé sa réserve sur ce hadith. Al-Albani note que ce hadith est très répandu dans les khutbas de Ramadan et que sa faiblesse est ignorée.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'Dans Taqrib al-Tahdhib : "\'Ali ibn Zayd ibn Jud\'an — da\'if. Sa mémoire est problématique dans plusieurs transmissions."' },
      { imam:IMAMS.dhahabi, jugement:'Dans Mizan : "Ali ibn Zayd ibn Jud\'an n\'est pas fort (laysa bi qawi). Ahmad ibn Hanbal l\'a affaibli."' },
      { imam:IMAMS.ahmad,   jugement:'Rapporté par Ibn Hajar que Ahmad ibn Hanbal a dit de \'Ali ibn Zayd : "da\'if al-hadith" (rapporteur de hadiths faibles).' }
    ]
  },
  sanad:{
    adala:   { statut:'daif',  detail:'\'Ali ibn Zayd ibn Jud\'an — affaibli par Ahmad, Ibn Hajar, Dhahabi et la majorité des imams du Jarh wa Ta\'dil. \'Adala compromise.' },
    dabt:    { statut:'daif',  detail:'Précision mémorielle insuffisante selon les muhaddithun. Ibn Khuzayma lui-même avait des réserves sur ce rapporteur.' },
    ittisal: { statut:'sahih', detail:'La chaîne est formellement continue — la faiblesse vient du rapporteur lui-même, pas d\'une rupture.' },
    shudhudh:{ statut:'daif',  detail:'Anomalie possible : les autres hadiths authentiques sur le Ramadan ne font pas cette division en trois tiers.' },
    illa:    { statut:'daif',  detail:'\'Illa : le texte semble être le résultat d\'un montage (tarkib) de plusieurs traditions sur la miséricorde, le pardon et la libération — séparément authentiques, combinées incorrectement.' }
  },
  note:'DA\'IF (Al-Albani, SD n°1569). Très répandu dans les khutbas de Ramadan — ne pas le citer comme parole du Prophète ﷺ.',
  keywords:['ramadan','tiers','miséricorde','pardon','liberation','feu','رمضان','رحمة','مغفرة','عتق'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'daif:travail_eternel',
  ar:'اعْمَلْ لِدُنْيَاكَ كَأَنَّكَ تَعِيشُ أَبَدًا، وَاعْمَلْ لِآخِرَتِكَ كَأَنَّكَ تَمُوتُ غَدًا',
  fr:'Travaille pour ce monde comme si tu vivais éternellement, et travaille pour ton au-delà comme si tu mourais demain.',
  source:'Attribué à Ibn Umar — Faible selon Al-Albani', book:'—', numero:null,
  grade:'DAIF', grade_ar:'ضَعِيف إِلَى مَوْضُوع',
  albani:{
    hukm:'ضَعِيف إلى موضوع', hukm_fr:'DA\'IF à MAWDU\' — Faible à inventé',
    ref:'SD — Da\'if al-Jami n°177',
    raisonnement:'Al-Albani dans Da\'if al-Jami n°177 : ce texte est attribué tantôt au Prophète ﷺ, tantôt à Ibn Umar — signe de confusion dans la transmission. Certains imams le jugent mawdu\'. Al-Albani le classe entre da\'if et mawdu\'. De plus, le sens même du hadith est problématique : il semble contredire le zuhd que le Prophète ﷺ recommandait.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'A mentionné ce hadith sans l\'authentifier. L\'attribution varie selon les versions — signe d\'irrégularité dans la transmission.' },
      { imam:IMAMS.dhahabi, jugement:'Dans Mizan : a signalé des problèmes dans les voies de ce texte sans pouvoir l\'authentifier dans aucune version.' }
    ]
  },
  sanad:{
    adala:   { statut:'daif',  detail:'Rapporteurs problématiques dans toutes les voies examinées par Al-Albani. Attribution confuse entre hadith prophétique et parole de Compagnon.' },
    dabt:    { statut:'daif',  detail:'La confusion dans l\'attribution (Prophète ﷺ vs Ibn Umar) est elle-même une preuve de défaillance mémorielle dans la transmission.' },
    ittisal: { statut:'daif',  detail:'Chaînes interrompues ou contenant des rapporteurs inconnus selon Al-Albani.' },
    shudhudh:{ statut:'daif',  detail:'Anomalie textuelle majeure : ce hadith semble contredire "Sois dans ce monde comme un étranger" (Bukhari n°6416) — contradiction interne dans la Sunna impossible si authentique.' },
    illa:    { statut:'daif',  detail:'\'Illa : texte probablement forgé à partir de deux concepts authentiques (travail en ce monde + travail pour l\'au-delà) combinés de façon incorrecte.' }
  },
  note:'DA\'IF à MAWDU\' (Al-Albani). Sens théologiquement suspect. Préférer Bukhari n°6416.',
  badil:{ ar:'كُنْ فِي الدُّنْيَا كَأَنَّكَ غَرِيبٌ أَوْ عَابِرُ سَبِيلٍ', source:'Sahih Al-Bukhari n°6416', fr:'Sois dans ce monde comme un étranger ou un passant.' },
  keywords:['travail','monde','eternel','akhira','dunya','اعمل','آخرة','eternellement'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

/* ═══════════════════════════════════════════════════
   BLOC C — HADITHS MAWDU' (INVENTÉS/FORGÉS)
   Avec identification des fabricateurs et réfutation
═══════════════════════════════════════════════════ */

{
  id:'mawdu:science_chine',
  ar:'اطْلُبُوا الْعِلْمَ وَلَوْ بِالصِّينِ',
  fr:'Cherchez le savoir même en Chine.',
  source:'Rapporté sans chaîne valide — Inventé', book:'—', numero:null,
  grade:'MAWDU', grade_ar:'مَوْضُوع',
  albani:{
    hukm:'مَوْضُوع', hukm_fr:'MAWDU\' — Inventé/Forgé',
    ref:'SD n°416 — Da\'if al-Jami n°905',
    raisonnement:'Al-Albani dans SD n°416 : la voie principale passe par Abu \'Atika Tarif ibn Salman qui a été unanimement jugé kadhdhab (menteur délibéré) par les imams. Al-Bukhari : "munkar al-hadith". Ibn Hibban : "il fabrique des hadiths". Aucune voie alternative valable. Al-Albani a examiné toutes les prétentions d\'authenticité et les a toutes réfutées une par une.',
    imams_cites:[
      { imam:IMAMS.bukhari,  jugement:'Sur Abu \'Atika Tarif ibn Salman : "Munkar al-hadith" — terme technique signifiant que ses hadiths sont rejetés systématiquement.' },
      { imam:IMAMS.ibnhiban, jugement:'Dans Kitab al-Majruhin : "Abu \'Atika fabrique des hadiths (yada\' al-hadith). Il n\'est pas permis de rapporter de lui."' },
      { imam:IMAMS.ibnjawzi, jugement:'Dans Al-Mawdu\'at : "Ce hadith est mawdu\'. Abu \'Atika est kadhdhab (menteur)."' }
    ]
  },
  sanad:{
    adala:   { statut:'daif',  detail:'Abu \'Atika Tarif ibn Salman : kadhdhab (menteur délibéré) selon Al-Bukhari, Ibn Hibban, Ibn al-Jawzi. \'Adala ABSENTE — rapporteur exclu de la transmission.' },
    dabt:    { statut:'daif',  detail:'Dabt sans objet pour un rapporteur kadhdhab. Un menteur ne peut avoir de "précision mémorielle" dans ses transmissions.' },
    ittisal: { statut:'daif',  detail:'Même si la chaîne était formellement continue, la présence d\'un kadhdhab annule tout bénéfice.' },
    shudhudh:{ statut:'daif',  detail:'Anomalie textuelle : la Chine était inconnue ou marginale dans l\'univers mental des arabes du 7ème siècle. Ce détail géographique semble anachronique.' },
    illa:    { statut:'daif',  detail:'\'Illa grave : existence d\'un rapporteur kadhdhab = fabrication délibérée = mawdu\' certain.' }
  },
  note:'INVENTÉ (Al-Albani, SD n°416). Le rapporteur principal est un menteur confirmé. Ne jamais citer ce hadith.',
  badil:{ ar:'طَلَبُ الْعِلْمِ فَرِيضَةٌ عَلَى كُلِّ مُسْلِمٍ', source:'Sunan Ibn Majah n°224 — Authentifié par Al-Albani', fr:'Chercher le savoir est une obligation pour tout musulman.' },
  keywords:['science','savoir','chine','اطلبوا العلم','الصين','cherche science chine'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'mawdu:mariage_moitie',
  ar:'النِّكَاحُ نِصْفُ الإِيمَانِ',
  fr:'Le mariage est la moitié de la foi.',
  source:'Chaîne brisée — Inventé', book:'—', numero:null,
  grade:'MAWDU', grade_ar:'مَوْضُوع',
  albani:{
    hukm:'مَوْضُوع', hukm_fr:'MAWDU\' — Inventé',
    ref:'SD n°4 — Da\'if al-Jami n°5901',
    raisonnement:'Al-Albani dans SD n°4 (premier hadith de la série des da\'ifa) : la chaîne est munqati\'a (brisée). Aucun lien entre le Compagnon rapporteur et le Tabi\'i intermédiaire. Al-Albani précise que le texte authentique sur ce sujet utilise "istakmal nisf al-iman" (a complété la moitié) — formulation différente et plus nuancée, attribuée à un Tabi\'i, non au Prophète.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'Dans al-Fath : "La formulation \'al-nikah nisf al-iman\' n\'est pas authentique telle quelle. Le texte rapporté de façon hasan est \'man tazawwaj faqad istakmal nisf al-iman\'."' },
      { imam:IMAMS.baihaqi, jugement:'A rapporté le hadith alternatif avec la formulation "istakmal" via une voie hasan, tout en reconnaissant la faiblesse de la formulation "nisf al-iman" directe.' }
    ]
  },
  sanad:{
    adala:   { statut:'daif',  detail:'Rapporteur intermédiaire inconnu dans la chaîne principale. L\'anonymat (jahalat al-rawi) invalide la transmission.' },
    dabt:    { statut:'daif',  detail:'Impossible d\'évaluer le dabt d\'un rapporteur inconnu (majhul al-\'ayn).' },
    ittisal: { statut:'daif',  detail:'Munqati\' — rupture confirmée dans la chaîne. Absence d\'un maillon intermédiaire entre le Compagnon et le Tabi\'i.' },
    shudhudh:{ statut:'daif',  detail:'Anomalie textuelle : la formulation diffère de celle rapportée par Al-Baihaqi en voie hasan. Contradiction interne.' },
    illa:    { statut:'daif',  detail:'\'Illa : probable confusion entre une parole d\'un Tabi\'i et un hadith prophétique lors de la transmission.' }
  },
  note:'INVENTÉ telle quelle (Al-Albani, SD n°4). Citer la formulation authentique à la place.',
  badil:{ ar:'مَنْ تَزَوَّجَ فَقَدِ اسْتَكْمَلَ نِصْفَ الإِيمَانِ فَلْيَتَّقِ اللَّهَ فِي النِّصْفِ الْبَاقِي', source:'Al-Baihaqi — Hasan selon Al-Albani', fr:'Celui qui se marie a complété la moitié de sa foi. Qu\'il craigne Allah pour l\'autre moitié.' },
  keywords:['mariage','moitié','foi','nikah','نكاح','نصف الإيمان'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'mawdu:patrie_foi',
  ar:'حُبُّ الْوَطَنِ مِنَ الإِيمَانِ',
  fr:'L\'amour de la patrie fait partie de la foi.',
  source:'Sans aucun fondement — Inventé', book:'—', numero:null,
  grade:'MAWDU', grade_ar:'مَوْضُوع',
  albani:{
    hukm:'لَا أَصْلَ لَهُ', hukm_fr:'SANS FONDEMENT — La asla lahu',
    ref:'SD n°36',
    raisonnement:'Al-Albani dans SD n°36 : "Ce hadith est sans aucun fondement (la asla lahu) dans les livres de Sunna". Il n\'a aucune chaîne de transmission, même faible. Ce texte est probablement forgé à l\'époque du nationalisme arabe (19ème-20ème siècle) pour légitimer les mouvements nationalistes. Al-Albani le juge plus grave qu\'un simple hadith faible : c\'est une fabrication sans trace.',
    imams_cites:[
      { imam:IMAMS.dhahabi, jugement:'Ne mentionne ce hadith nulle part dans ses compilations — signe qu\'il n\'avait aucune chaîne connue de son temps.' },
      { imam:IMAMS.hajar,   jugement:'Absent de l\'ensemble de ses oeuvres de takhrij — aucune chaîne n\'était connue avant l\'ère moderne.' }
    ]
  },
  sanad:{
    adala:   { statut:'mafqud', detail:'ABSENT : aucune chaîne de transmission identifiée. Aucun rapporteur à évaluer. La asla lahu (sans fondement).' },
    dabt:    { statut:'mafqud', detail:'ABSENT : sans chaîne, le critère du dabt est sans objet.' },
    ittisal: { statut:'mafqud', detail:'ABSENT : aucune transmission identifiable. Texte surgissant de nulle part dans les sources islamiques.' },
    shudhudh:{ statut:'daif',   detail:'Anomalie idéologique majeure : la wala\' (loyauté) islamique est pour Allah, Son Messager et les croyants — non pour une entité géographique ou nationale.' },
    illa:    { statut:'daif',   detail:'\'Illa idéologique : forgé pour servir les mouvements nationalistes arabes du 19ème siècle — contradiction avec les fondements de l\'\'aqida islamique.' }
  },
  note:'SANS FONDEMENT (Al-Albani, SD n°36). "La asla lahu" — pas même une chaîne faible. Probablement forgé à l\'époque moderne.',
  keywords:['patrie','nationalisme','amour','foi','وطن','إيمان','nation','حب الوطن'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'mawdu:difference_opinion',
  ar:'اخْتِلَافُ أُمَّتِي رَحْمَةٌ',
  fr:'La divergence d\'opinion de ma communauté est une miséricorde.',
  source:'Sans chaîne valide — Inventé', book:'—', numero:null,
  grade:'MAWDU', grade_ar:'مَوْضُوع',
  albani:{
    hukm:'لَا يَصِحُّ', hukm_fr:'LA YASIHHU — Ne peut être authentifié',
    ref:'SD n°57 — Da\'if al-Jami n°230',
    raisonnement:'Al-Albani dans SD n°57 : "Ce hadith n\'est pas authentique selon les imams du hadith." Ibn Hazm : "C\'est un hadith batil (nul) qui n\'a pas de chaîne (isnad) du tout." Al-Suyuti : "Je n\'ai pas trouvé d\'isnad pour ce hadith." Al-Albani insiste : ce hadith est utilisé pour paralyser le Jarh wa Ta\'dil et légitimer les innovations — son usage même est suspect.',
    imams_cites:[
      { imam:IMAMS.hajar,   jugement:'A cherché un isnad pour ce hadith sans succès. Dans al-Fath : "Ce hadith est non authentifié (ghayr sabit)."' },
      { imam:IMAMS.nawawi,  jugement:'Dans al-Majmu\' : "Les muhaddithun n\'ont pas trouvé d\'isnad pour ce hadith." Ne peut servir de preuve.' },
      { imam:IMAMS.dhahabi, jugement:'Absent de toutes ses compilations de hadiths — signe qu\'aucune chaîne n\'était connue.' }
    ]
  },
  sanad:{
    adala:   { statut:'mafqud', detail:'ABSENT : aucun isnad identifié par Al-Albani, Ibn Hazm, Al-Suyuti ou aucun imam du hadith. Texte sans transmission.' },
    dabt:    { statut:'mafqud', detail:'ABSENT : sans rapporteur identifiable, le critère du dabt est sans objet.' },
    ittisal: { statut:'mafqud', detail:'ABSENT : aucune chaîne. Texte surgissant sans transmission identifiable dans la littérature du hadith.' },
    shudhudh:{ statut:'daif',   detail:'Anomalie textuelle grave : contredit directement "wa la takhtalifou fa tastakbiru" (ne vous divisez pas) — Coran 8:46. Le Coran ordonne l\'unité, pas la glorification de la division.' },
    illa:    { statut:'daif',   detail:'\'Illa idéologique : ce "hadith" sert précisément à invalider le Jarh wa Ta\'dil — la discipline qui le réfute. Outil rhétorique, non parole prophétique.' }
  },
  note:'SANS ISNAD (Al-Albani, SD n°57). Ibn Hazm : "Batil — pas d\'isnad du tout." Outil de déstabilisation du Jarh wa Ta\'dil.',
  badil:{ ar:'لَا تَجْتَمِعُ أُمَّتِي عَلَى ضَلَالَةٍ', source:'At-Tirmidhi — Authentifié par Al-Albani', fr:'Ma communauté ne s\'accordera jamais sur une erreur.' },
  keywords:['différence','divergence','opinion','rahma','miséricorde','اختلاف','رحمة','أمتي'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},

{
  id:'mawdu:encre_sang',
  ar:'مِدَادُ الْعُلَمَاءِ أَفْضَلُ مِنْ دِمَاءِ الشُّهَدَاءِ',
  fr:'L\'encre des savants est plus précieuse que le sang des martyrs.',
  source:'Aucune chaîne valide — Inventé', book:'—', numero:null,
  grade:'MAWDU', grade_ar:'مَوْضُوع',
  albani:{
    hukm:'لَا أَصْلَ لَهُ', hukm_fr:'SANS FONDEMENT — La asla lahu',
    ref:'SD n°3018',
    raisonnement:'Al-Albani dans SD n°3018 : "Ce hadith n\'a aucun fondement (la asla lahu)." Aucune chaîne connue des premiers siècles. Al-Albani précise qu\'il est répandu sous forme de sentence (hikma) et non de hadith dans les plus anciens textes — quelqu\'un l\'a ensuite forgé en hadith prophétique.',
    imams_cites:[
      { imam:IMAMS.dhahabi, jugement:'Ne le mentionne dans aucune de ses compilations de hadiths — absent de toute la littérature classique du hadith.' },
      { imam:IMAMS.ibnjawzi,jugement:'Dans al-Mawdu\'at : texte de ce type (valorisation extrême des savants sur les martyrs) est suspect — contredit la hiérarchie islamique des actes.' }
    ]
  },
  sanad:{
    adala:   { statut:'mafqud', detail:'ABSENT : aucun rapporteur, aucune chaîne. La asla lahu selon Al-Albani.' },
    dabt:    { statut:'mafqud', detail:'ABSENT : sans chaîne, critère inapplicable.' },
    ittisal: { statut:'mafqud', detail:'ABSENT : aucune transmission identifiable dans la littérature classique.' },
    shudhudh:{ statut:'daif',   detail:'Anomalie théologique : placer l\'encre des savants au-dessus du sang des martyrs contredit plusieurs hadiths authentiques sur le martyre.' },
    illa:    { statut:'daif',   detail:'\'Illa : probable transformation d\'une parole de sagesse humaine en hadith prophétique à une époque indéterminée.' }
  },
  note:'SANS FONDEMENT (Al-Albani, SD n°3018). Très répandu malgré l\'absence totale d\'isnad.',
  keywords:['encre','savants','sang','martyrs','مداد','علماء','دماء','شهداء'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
}
,{
  id:'bukhari:2',
  ar:'إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى',
  fr:'Les actes ne valent que par les intentions, et chaque homme n\'aura que ce qu\'il a voulu.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°1 — Sahih Muslim n°1907',
  resume:'Hadith fondateur — premier hadith de Bukhari. Principe de l\'intention (Niyyah).',
  keywords:['intention','niyyah','actes','نية','الأعمال','نوى','مقاصد'],
  url_dorar:'https://dorar.net/hadith/sharh/2', url_sunnah:'https://sunnah.com/bukhari:1'
},
{
  id:'bukhari:3',
  ar:'الإِيمَانُ بِضْعٌ وَسِتُّونَ شُعْبَةً، وَالحَيَاءُ شُعْبَةٌ مِنَ الإِيمَانِ',
  fr:'La foi a plus de soixante branches, et la pudeur est une branche de la foi.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°9 — Sahih Muslim n°35',
  resume:'La pudeur (Haya) est une branche essentielle de la foi.',
  keywords:['foi','haya','pudeur','iman','branches','الإيمان','الحياء','شعبة'],
  url_dorar:'https://dorar.net/hadith/sharh/9', url_sunnah:'https://sunnah.com/bukhari:9'
},
{
  id:'muslim:1',
  ar:'لاَ يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ',
  fr:'Aucun de vous ne croit vraiment tant qu\'il n\'aime pas pour son frère ce qu\'il aime pour lui-même.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°13 — Sahih Muslim n°45',
  resume:'Condition de la foi parfaite : aimer pour son frère musulman ce qu\'on aime pour soi.',
  keywords:['amour','frere','foi','ukhuwwa','fraternite','يحب','أخيه','يؤمن'],
  url_dorar:'https://dorar.net/hadith/sharh/13', url_sunnah:'https://sunnah.com/bukhari:13'
},
{
  id:'bukhari:4',
  ar:'مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ',
  fr:'Que celui qui croit en Allah et au Jour Dernier dise une bonne parole ou qu\'il se taise.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°6018 — Sahih Muslim n°47',
  resume:'La parole et le silence — règle d\'or du musulman croyant.',
  keywords:['parole','silence','langue','kalim','صمت','خيرا','يصمت','يؤمن'],
  url_dorar:'https://dorar.net/hadith/sharh/6018', url_sunnah:'https://sunnah.com/bukhari:6018'
},
{
  id:'tirmidhi:1',
  ar:'اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ، وَأَتْبِعِ السَّيِّئَةَ الْحَسَنَةَ تَمْحُهَا، وَخَالِقِ النَّاسَ بِخُلُقٍ حَسَنٍ',
  fr:'Crains Allah où que tu sois. Fais suivre la mauvaise action d\'une bonne, elle l\'effacera. Et traite les gens avec un beau comportement.',
  grade:'HASAN', grade_ar:'حسن', grade_label:'HASAN — Bon',
  reference:'Sunan At-Tirmidhi n°1987 — Hasan selon Al-Albani',
  resume:'Trois principes : Taqwa, effacement des péchés par les bonnes oeuvres, belle conduite.',
  keywords:['taqwa','piete','bonne action','comportement','تق الله','السيئة','الحسنة','حسن'],
  url_dorar:'https://dorar.net/hadith/sharh/3973', url_sunnah:'https://sunnah.com/tirmidhi:1987'
},
{
  id:'muslim:2',
  ar:'كُلُّ أَمْرٍ ذِي بَالٍ لاَ يُبْدَأُ فِيهِ بِـ بِسْمِ اللَّهِ فَهُوَ أَقْطَعُ',
  fr:'Toute affaire importante qui ne commence pas par Bismillah est coupée (de toute bénédiction).',
  grade:'HASAN', grade_ar:'حسن', grade_label:'HASAN — Bon',
  reference:'Ahmad — Hasan selon Al-Albani dans Silsilat As-Sahiha n°1',
  resume:'Commencer toute affaire par Bismillah.',
  keywords:['bismillah','basmalah','debut','بسمله','بسم الله','بال','أقطع'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},
{
  id:'bukhari:5',
  ar:'إِنَّ اللَّهَ يُحِبُّ إِذَا عَمِلَ أَحَدُكُمْ عَمَلاً أَنْ يُتْقِنَهُ',
  fr:'Allah aime que lorsque l\'un de vous accomplit une oeuvre, il la fasse avec excellence.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Al-Bayhaqi — Sahih selon Al-Albani dans Silsilat As-Sahiha n°1113',
  resume:'L\'excellence (Itqan) dans le travail est aimée d\'Allah.',
  keywords:['excellence','travail','itqan','ihsan','يحب','يتقن','عمل','إتقان'],
  url_dorar:'https://dorar.net', url_sunnah:'https://dorar.net'
},
{
  id:'bukhari:6',
  ar:'الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ',
  fr:'Le musulman est celui dont les musulmans sont préservés de sa langue et de sa main.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°10 — Sahih Muslim n°40',
  resume:'Définition du vrai musulman : préserver autrui de ses paroles et ses actes.',
  keywords:['musulman','langue','main','islam','سلم','لسانه','يده','المسلم'],
  url_dorar:'https://dorar.net/hadith/sharh/10', url_sunnah:'https://sunnah.com/bukhari:10'
},
{
  id:'bukhari:7',
  ar:'لاَ يَدْخُلُ الْجَنَّةَ مَنْ كَانَ فِي قَلْبِهِ مِثْقَالُ ذَرَّةٍ مِنْ كِبْرٍ',
  fr:'N\'entrera pas au paradis celui qui a dans le coeur l\'équivalent d\'un atome d\'orgueil.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°91',
  resume:'L\'orgueil (Kibr) est un obstacle majeur à l\'entrée au paradis.',
  keywords:['orgueil','kibr','paradis','coeur','كبر','الجنة','قلبه','ذرة'],
  url_dorar:'https://dorar.net/hadith/sharh/320', url_sunnah:'https://sunnah.com/muslim:91'
},
{
  id:'bukhari:8',
  ar:'مَنْ صَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ',
  fr:'Celui qui jeûne le Ramadan par foi et en espérant la récompense, ses péchés passés lui seront pardonnés.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°38 — Sahih Muslim n°760',
  resume:'La récompense du jeûne du Ramadan avec foi et espoir : pardon des péchés passés.',
  keywords:['ramadan','jeune','pardon','siyam','رمضان','صام','غفر','ذنب','إيمانا','احتسابا'],
  url_dorar:'https://dorar.net/hadith/sharh/38', url_sunnah:'https://sunnah.com/bukhari:38'
},
{
  id:'bukhari:9',
  ar:'مَنْ قَامَ رَمَضَانَ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ',
  fr:'Celui qui accomplit la prière nocturne de Ramadan par foi et en espérant la récompense, ses péchés passés lui seront pardonnés.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°37 — Sahih Muslim n°759',
  resume:'La prière nocturne de Ramadan (Tarawih/Qiyam) avec foi efface les péchés passés.',
  keywords:['ramadan','priere de nuit','tarawih','qiyam','رمضان','قام','غفر','إيمانا'],
  url_dorar:'https://dorar.net/hadith/sharh/37', url_sunnah:'https://sunnah.com/bukhari:37'
},
{
  id:'bukhari:10',
  ar:'مَنْ قَامَ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ',
  fr:'Celui qui accomplit la prière de la Nuit du Destin par foi et en espérant la récompense, ses péchés passés lui seront pardonnés.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°35 — Sahih Muslim n°760',
  resume:'La Nuit du Destin (Laylat Al-Qadr) : meilleure que mille mois.',
  keywords:['laylat al qadr','nuit du destin','pardon','ليلة القدر','قام','غفر'],
  url_dorar:'https://dorar.net/hadith/sharh/35', url_sunnah:'https://sunnah.com/bukhari:35'
},
{
  id:'muslim:3',
  ar:'بُنِيَ الإِسْلاَمُ عَلَى خَمْسٍ: شَهَادَةِ أَنْ لاَ إِلَهَ إِلاَّ اللَّهُ وَأَنَّ مُحَمَّدًا رَسُولُ اللَّهِ، وَإِقَامِ الصَّلاَةِ، وَإِيتَاءِ الزَّكَاةِ، وَصَوْمِ رَمَضَانَ، وَحَجِّ الْبَيْتِ',
  fr:'L\'islam est bâti sur cinq piliers : témoigner qu\'il n\'y a de divinité qu\'Allah et que Muhammad est Son messager, accomplir la prière, acquitter la zakat, jeûner le Ramadan et faire le pèlerinage de la Maison.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°8 — Sahih Muslim n°16',
  resume:'Les cinq piliers de l\'Islam — fondement de la religion.',
  keywords:['piliers','islam','cinq','shahada','salat','zakat','hajj','sawm','بني','خمس','الإسلام','شهادة'],
  url_dorar:'https://dorar.net/hadith/sharh/8', url_sunnah:'https://sunnah.com/bukhari:8'
},
{
  id:'bukhari:11',
  ar:'خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ',
  fr:'Le meilleur d\'entre vous est celui qui apprend le Coran et l\'enseigne.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°5027',
  resume:'La noblesse de celui qui apprend et enseigne le Coran.',
  keywords:['coran','quran','apprendre','enseigner','خير','القرآن','تعلم','علم'],
  url_dorar:'https://dorar.net/hadith/sharh/5027', url_sunnah:'https://sunnah.com/bukhari:5027'
},
{
  id:'muslim:4',
  ar:'إِنَّ اللَّهَ لاَ يَنْظُرُ إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ، وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ',
  fr:'Allah ne regarde pas vos apparences ni vos richesses, mais Il regarde vos coeurs et vos actes.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°2564',
  resume:'Allah juge selon le coeur et les actes, non l\'apparence ni la richesse.',
  keywords:['coeur','apparence','actes','richesse','قلب','صور','أموال','أعمال','ينظر'],
  url_dorar:'https://dorar.net/hadith/sharh/2564', url_sunnah:'https://sunnah.com/muslim:2564'
},
{
  id:'bukhari:12',
  ar:'لاَ تَدْخُلُوا الْجَنَّةَ حَتَّى تُؤْمِنُوا، وَلاَ تُؤْمِنُوا حَتَّى تَحَابُّوا',
  fr:'Vous n\'entrerez pas au paradis tant que vous ne croirez pas, et vous ne croirez pas vraiment tant que vous ne vous aimerez pas mutuellement.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°54',
  resume:'Lien entre l\'amour mutuel, la foi et l\'entrée au paradis.',
  keywords:['amour','paradis','foi','fraternite','الجنة','تؤمنوا','تحابوا','ودوا'],
  url_dorar:'https://dorar.net/hadith/sharh/54', url_sunnah:'https://sunnah.com/muslim:54'
},
{
  id:'bukhari:13',
  ar:'مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ طَرِيقًا إِلَى الْجَنَّةِ',
  fr:'Celui qui prend un chemin pour chercher la connaissance, Allah lui facilite un chemin vers le paradis.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°2699',
  resume:'La quête du savoir islamique facilite le chemin vers le paradis.',
  keywords:['science','savoir','ilm','paradis','chemin','علم','طريقا','الجنة','سلك'],
  url_dorar:'https://dorar.net/hadith/sharh/6722', url_sunnah:'https://sunnah.com/muslim:2699'
},
{
  id:'bukhari:14',
  ar:'الدُّنْيَا سِجْنُ الْمُؤْمِنِ وَجَنَّةُ الْكَافِرِ',
  fr:'Le monde ici-bas est une prison pour le croyant et un paradis pour le mécréant.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°2956',
  resume:'Le statut du monde ici-bas (Dunya) pour le croyant et le mécréant.',
  keywords:['dunya','monde','prison','paradis','croyant','الدنيا','سجن','المؤمن','جنة','الكافر'],
  url_dorar:'https://dorar.net/hadith/sharh/7269', url_sunnah:'https://sunnah.com/muslim:2956'
},
{
  id:'bukhari:15',
  ar:'مَنْ كَظَمَ غَيْظًا وَهُوَ قَادِرٌ عَلَى أَنْ يُنْفِذَهُ دَعَاهُ اللَّهُ عَزَّ وَجَلَّ عَلَى رُؤُوسِ الْخَلاَئِقِ',
  fr:'Celui qui ravale sa colère alors qu\'il aurait pu l\'exprimer, Allah l\'appellera devant toutes les créatures.',
  grade:'HASAN', grade_ar:'حسن', grade_label:'HASAN — Bon',
  reference:'Abu Dawud n°4777 — Hasan selon Al-Albani',
  resume:'La vertu de maîtriser sa colère malgré la capacité de la laisser éclater.',
  keywords:['colere','patience','ghazab','maîtrise','كظم','غيظا','الله','الخلائق'],
  url_dorar:'https://dorar.net', url_sunnah:'https://sunnah.com/abudawud:4777'
},
{
  id:'bukhari:16',
  ar:'إِنَّ مِنْ أَشَدِّ النَّاسِ عَذَابًا يَوْمَ الْقِيَامَةِ الْمُصَوِّرُونَ',
  fr:'Parmi ceux qui recevront le châtiment le plus sévère au Jour du Jugement se trouvent ceux qui font des images (des êtres vivants).',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°5950 — Sahih Muslim n°2109',
  resume:'Interdiction des images d\'êtres animés — sévère avertissement.',
  keywords:['images','tasweer','interdiction','jugement','المصورون','عذابا','صور','القيامة'],
  url_dorar:'https://dorar.net/hadith/sharh/5950', url_sunnah:'https://sunnah.com/bukhari:5950'
},
{
  id:'bukhari:17',
  ar:'أَكْمَلُ الْمُؤْمِنِينَ إِيمَانًا أَحْسَنُهُمْ خُلُقًا وَخِيَارُكُمْ خِيَارُكُمْ لِنِسَائِهِمْ',
  fr:'Le plus parfait des croyants en foi est celui qui a le meilleur caractère, et les meilleurs d\'entre vous sont ceux qui traitent le mieux leurs femmes.',
  grade:'HASAN', grade_ar:'حسن', grade_label:'HASAN — Bon',
  reference:'Sunan At-Tirmidhi n°1162 — Hasan Sahih selon Al-Albani',
  resume:'Le bon caractère est le signe de la foi parfaite. Bien traiter son épouse.',
  keywords:['caractere','femme','epouse','foi','خلق','إيمانا','نسائهم','أكمل'],
  url_dorar:'https://dorar.net/hadith/sharh/3895', url_sunnah:'https://sunnah.com/tirmidhi:1162'
},
{
  id:'bukhari:18',
  ar:'الْمُؤْمِنُ لِلْمُؤْمِنِ كَالْبُنْيَانِ يَشُدُّ بَعْضُهُ بَعْضًا',
  fr:'Le croyant pour le croyant est comme un édifice dont les parties se soutiennent mutuellement.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°481 — Sahih Muslim n°2585',
  resume:'La solidarité et l\'entraide entre croyants.',
  keywords:['fraternite','entraide','solidarite','المؤمن','البنيان','يشد','أخوة'],
  url_dorar:'https://dorar.net/hadith/sharh/481', url_sunnah:'https://sunnah.com/bukhari:481'
},
{
  id:'bukhari:19',
  ar:'إِنَّ اللَّهَ رَفِيقٌ يُحِبُّ الرِّفْقَ فِي الأَمْرِ كُلِّهِ',
  fr:'Allah est Doux et Il aime la douceur en toute chose.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°6927 — Sahih Muslim n°2165',
  resume:'La douceur (Rifq) est aimée d\'Allah en toute circonstance.',
  keywords:['douceur','rifq','gentillesse','الله','رفيق','الرفق','يحب'],
  url_dorar:'https://dorar.net/hadith/sharh/6927', url_sunnah:'https://sunnah.com/bukhari:6927'
},
{
  id:'bukhari:20',
  ar:'مَنْ لاَ يَرْحَمُ لاَ يُرْحَمُ',
  fr:'Celui qui n\'est pas miséricordieux n\'obtiendra pas de miséricorde.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°5997 — Sahih Muslim n°2318',
  resume:'La miséricorde envers les créatures est une condition pour obtenir la miséricorde divine.',
  keywords:['misericorde','rahma','compassion','يرحم','لا يرحم','رحمة'],
  url_dorar:'https://dorar.net/hadith/sharh/5997', url_sunnah:'https://sunnah.com/bukhari:5997'
},
{
  id:'bukhari:21',
  ar:'صِلَةُ الرَّحِمِ تَزِيدُ فِي الْعُمُرِ وَتَدْفَعُ مِيتَةَ السُّوءِ',
  fr:'Maintenir les liens de parenté prolonge la vie et repousse la mauvaise mort.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°5986 — Sahih Muslim n°2557',
  resume:'Les liens de parenté (Silat Ar-Rahim) prolongent la vie et apportent la bénédiction.',
  keywords:['famille','liens','rahim','silah','صلة الرحم','العمر','رحم','قرابة'],
  url_dorar:'https://dorar.net/hadith/sharh/5986', url_sunnah:'https://sunnah.com/bukhari:5986'
},
{
  id:'bukhari:22',
  ar:'أَفْضَلُ الصَّدَقَةِ أَنْ تَصَدَّقَ وَأَنْتَ صَحِيحٌ شَحِيحٌ تَأْمُلُ الْغِنَى وَتَخْشَى الْفَقْرَ',
  fr:'La meilleure aumône est celle que tu donnes quand tu es en bonne santé, avare (par nature), que tu espères la richesse et que tu crains la pauvreté.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°1419',
  resume:'La meilleure Sadaqa : donner de son vivant et en bonne santé.',
  keywords:['sadaqa','aumone','charite','generosité','الصدقة','صحيح','شحيح','الغنى','الفقر'],
  url_dorar:'https://dorar.net/hadith/sharh/1419', url_sunnah:'https://sunnah.com/bukhari:1419'
},
{
  id:'bukhari:23',
  ar:'الْحَلاَلُ بَيِّنٌ وَالْحَرَامُ بَيِّنٌ وَبَيْنَهُمَا أُمُورٌ مُشْتَبِهَاتٌ',
  fr:'Le licite est clair, l\'illicite est clair, et entre les deux il y a des choses ambiguës.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°52 — Sahih Muslim n°1599',
  resume:'Principe du Halal, Haram et des zones ambiguës (Shubuhaat).',
  keywords:['halal','haram','licite','illicite','ambigu','الحلال','الحرام','مشتبهات','بين'],
  url_dorar:'https://dorar.net/hadith/sharh/52', url_sunnah:'https://sunnah.com/bukhari:52'
},
{
  id:'bukhari:24',
  ar:'لاَ ضَرَرَ وَلاَ ضِرَارَ',
  fr:'Pas de préjudice et pas d\'acte dommageable (en Islam).',
  grade:'HASAN', grade_ar:'حسن', grade_label:'HASAN — Bon',
  reference:'Ibn Majah n°2340 — Hasan selon Al-Albani',
  resume:'Règle d\'or de la jurisprudence islamique : interdiction de causer du tort.',
  keywords:['prejudice','tort','dommage','fiqh','ضرر','ضرار','لا ضرر'],
  url_dorar:'https://dorar.net', url_sunnah:'https://sunnah.com/ibnmajah:2340'
},
{
  id:'bukhari:25',
  ar:'إِنَّ مِنَ الْبَيَانِ لَسِحْرًا',
  fr:'Certains discours éloquents ont un effet comparable à la magie.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°5767',
  resume:'Avertissement sur le pouvoir trompeur de l\'éloquence.',
  keywords:['eloquence','parole','discours','magie','البيان','سحرا','لسان'],
  url_dorar:'https://dorar.net/hadith/sharh/5767', url_sunnah:'https://sunnah.com/bukhari:5767'
},
{
  id:'bukhari:26',
  ar:'مَنْ غَشَّنَا فَلَيْسَ مِنَّا',
  fr:'Celui qui nous trompe n\'est pas des nôtres.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°101',
  resume:'La tromperie et la fraude sont incompatibles avec l\'appartenance à l\'Islam.',
  keywords:['tromperie','fraude','ghish','honnete','غش','غشنا','ليس منا'],
  url_dorar:'https://dorar.net/hadith/sharh/393', url_sunnah:'https://sunnah.com/muslim:101'
},
{
  id:'bukhari:27',
  ar:'يَسِّرُوا وَلاَ تُعَسِّرُوا وَبَشِّرُوا وَلاَ تُنَفِّرُوا',
  fr:'Facilitez et ne compliquez pas. Annoncez la bonne nouvelle et ne faites pas fuir.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°69 — Sahih Muslim n°1734',
  resume:'Principe de facilitation dans la Da\'wah et l\'enseignement islamique.',
  keywords:['facilite','dawah','enseignement','يسروا','تعسروا','بشروا','تنفروا'],
  url_dorar:'https://dorar.net/hadith/sharh/69', url_sunnah:'https://sunnah.com/bukhari:69'
},
{
  id:'bukhari:28',
  ar:'خَيْرُ الْقُرُونِ قَرْنِي ثُمَّ الَّذِينَ يَلُونَهُمْ ثُمَّ الَّذِينَ يَلُونَهُمْ',
  fr:'La meilleure génération est la mienne (les Compagnons), puis ceux qui les suivent, puis ceux qui les suivent.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°2651 — Sahih Muslim n°2533',
  resume:'La supériorité des trois premières générations (Salaf) en Islam.',
  keywords:['salaf','compagnons','generation','sahaba','خير القرون','قرني','يلونهم'],
  url_dorar:'https://dorar.net/hadith/sharh/2651', url_sunnah:'https://sunnah.com/bukhari:2651'
},
{
  id:'bukhari:29',
  ar:'تَسَحَّرُوا فَإِنَّ فِي السَّحُورِ بَرَكَةً',
  fr:'Prenez le repas de l\'aube (Suhur), car il y a une bénédiction dans ce repas.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Al-Bukhari n°1923 — Sahih Muslim n°1095',
  resume:'L\'importance du Suhur (repas avant l\'aube) pendant le Ramadan.',
  keywords:['suhur','ramadan','aube','baraka','سحور','السحور','بركة','تسحروا'],
  url_dorar:'https://dorar.net/hadith/sharh/1923', url_sunnah:'https://sunnah.com/bukhari:1923'
},
{
  id:'bukhari:30',
  ar:'كُلُّ بِدْعَةٍ ضَلاَلَةٌ وَكُلُّ ضَلاَلَةٍ فِي النَّارِ',
  fr:'Toute innovation (Bid\'ah) est un égarement, et tout égarement mène au feu.',
  grade:'SAHIH', grade_ar:'صحيح', grade_label:'SAHIH — Authentique',
  reference:'Sahih Muslim n°867 — An-Nasa\'i n°1578',
  resume:'Avertissement contre les innovations en religion (Bid\'ah).',
  keywords:['bidah','innovation','egarement','feu','بدعة','ضلالة','النار','كل بدعة'],
  url_dorar:'https://dorar.net/hadith/sharh/1578', url_sunnah:'https://sunnah.com/muslim:867'
}

]; /* fin HADITH_DATABASE */


/* ════════════════════════════════════════════════════════════════════
   § 3 — MOTEUR DE CHARGEMENT loadHadithDatabase()
════════════════════════════════════════════════════════════════════ */

function loadHadithDatabase(onSuccess, onError) {
  return new Promise(function(resolve, reject) {
    try {
      _indexDatabase(HADITH_DATABASE);
      MIZAN_DB_LOADED = true;
      console.log('[Al Mizan] DB v2 chargee : ' + HADITH_DATABASE.length + ' hadiths avec analyse complète du Sanad');
      if (onSuccess) onSuccess(HADITH_DATABASE);
      resolve(HADITH_DATABASE);
    } catch(err) {
      console.error('[Al Mizan] Erreur DB :', err);
      if (onError) onError(err);
      reject(err);
    }
  });
}

/* ════════════════════════════════════════════════════════════════════
   § 4 — MOTEUR DE RECHERCHE
════════════════════════════════════════════════════════════════════ */

var _searchIndex = {};
var _gradeIndex  = { SAHIH:[], HASAN:[], DAIF:[], MAWDU:[], INCONNU:[] };

function _indexDatabase(db) {
  _searchIndex = {};
  _gradeIndex  = { SAHIH:[], HASAN:[], DAIF:[], MAWDU:[], INCONNU:[] };
  db.forEach(function(h, idx) {
    var g = h.grade || 'INCONNU';
    if (_gradeIndex[g]) _gradeIndex[g].push(idx);
    else _gradeIndex[g] = [idx];
    if (h.keywords) h.keywords.forEach(function(k){ _addToIndex(k, idx); });
    _tokenize(h.fr || '').forEach(function(w){ _addToIndex(w, idx); });
    _addToIndex(h.id, idx);
    _tokenize(h.source || '').forEach(function(w){ _addToIndex(w, idx); });
    if (h.ar) _addToIndex(h.ar, idx);
  });
}

function _addToIndex(word, idx) {
  var w = _normalize(word);
  if (!w || w.length < 2) return;
  if (!_searchIndex[w]) _searchIndex[w] = [];
  if (_searchIndex[w].indexOf(idx) === -1) _searchIndex[w].push(idx);
}

function searchHadith(query, options) {
  options = options || {};
  var limit = options.limit || 5;
  var grade = options.grade || null;
  if (!query || query.length < 2) return [];
  var queryNorm  = _normalize(query);
  var queryWords = _tokenize(query);
  var scores = {};
  queryWords.forEach(function(word) {
    var wn = _normalize(word);
    if (!wn) return;
    if (_searchIndex[wn]) {
      _searchIndex[wn].forEach(function(idx){ scores[idx] = (scores[idx]||0) + 3; });
    }
    Object.keys(_searchIndex).forEach(function(key) {
      if (key !== wn && (key.indexOf(wn) === 0 || wn.indexOf(key) === 0)) {
        _searchIndex[key].forEach(function(idx){ scores[idx] = (scores[idx]||0) + 1; });
      }
    });
  });
  HADITH_DATABASE.forEach(function(h, idx) {
    if (_normalize(h.fr||'').indexOf(queryNorm) !== -1) scores[idx] = (scores[idx]||0) + 5;
    if ((h.ar||'').indexOf(query) !== -1)               scores[idx] = (scores[idx]||0) + 4;
    if (_normalize(h.id).indexOf(queryNorm) !== -1)     scores[idx] = (scores[idx]||0) + 2;
  });
  var candidates = Object.keys(scores).map(function(idx) {
    return { hadith: HADITH_DATABASE[parseInt(idx)], score: scores[idx] };
  });
  if (grade) candidates = candidates.filter(function(c){ return c.hadith && c.hadith.grade === grade.toUpperCase(); });
  candidates.sort(function(a,b){ return b.score - a.score; });
  return candidates.filter(function(c){ return c.score >= 1; }).slice(0, limit).map(function(c){ return c.hadith; });
}

function searchHadithForApp(rawInput) {
  if (!rawInput || rawInput.trim().length < 3) return null;
  var results = searchHadith(rawInput, { limit:1 });
  if (!results.length) return null;
  var h = results[0];
  return {
    grade:           h.grade,
    grade_ar:        h.grade_ar,
    grade_label:     _gradeLabel(h.grade),
    grade_color:     _gradeColor(h.grade),
    reference:       (h.albani && h.albani.ref) || (h.source + (h.numero ? ' n\u00B0'+h.numero : '')),
    resume:          h.fr,
    ar:              h.ar,
    isnad:           _buildIsnadChainSpans(h),
    isnad_check:     _buildSanadChecklist(h),
    analyse:         _buildAnalyseText(h),
    avis_savants:    _buildAvisSavants(h),
    albani:          h.albani || null,
    source_url:      h.url_sunnah || 'https://dorar.net',
    badil:           h.badil || null,
    db_source:       'MIZAN DB v' + MIZAN_DB_VERSION
  };
}

/* ════════════════════════════════════════════════════════════════════
   § 5 — HELPERS
════════════════════════════════════════════════════════════════════ */

function _normalize(s) {
  if (!s) return '';
  return ('' + s).toLowerCase()
    .replace(/[àâä]/g,'a').replace(/[éèêë]/g,'e').replace(/[ïî]/g,'i')
    .replace(/[ôö]/g,'o').replace(/[ùûü]/g,'u').replace(/ç/g,'c')
    .replace(/[\u064B-\u065F]/g,'')
    .replace(/[^a-z0-9\u0600-\u06FF\s]/g,'').replace(/\s+/g,' ').trim();
}

function _tokenize(text) {
  if (!text) return [];
  var stopwords = ['le','la','les','de','du','des','un','une','et','en','au','aux','par','sur','que','qui','dans','il','elle','ils','est','sont','pas','ne','se','ce','ou','car','si','je','tu','on','pour','avec'];
  return _normalize(text).split(' ').filter(function(w){ return w.length >= 2 && stopwords.indexOf(w) === -1; });
}

function _gradeLabel(grade) {
  var map = { 'SAHIH':'SAHIH — Authentique', 'HASAN':'HASAN — Bon', 'DAIF':"DA'IF — Faible", 'MAWDU':"MAWDU' — Inventé", 'INCONNU':'INCONNU — Non vérifié' };
  return map[grade] || grade;
}

function _gradeColor(grade) {
  var map = { 'SAHIH':'#22c55e', 'HASAN':'#4ade80', 'DAIF':'#f59e0b', 'MAWDU':'#ef4444', 'INCONNU':'rgba(201,168,76,.5)' };
  return map[grade] || '#888';
}

function _buildIsnadChainSpans(h) {
  /* TOUJOURS des <span> colores pour le Parchemin RTL */
  var g = h.grade || 'INCONNU';
  var src = h.source || '';
  var rw = h.rawi || '';
  var isSahih = (g==='SAHIH'||g==='HASAN');
  var rwCol = isSahih ? '#22c55e' : (g==='MAWDU'?'#e63946':'#f59e0b');
  var out = '';
  if(src) out += '<span style="color:#d4af37">'+src+'</span>';
  if(rw)  out += ' <span style="color:'+rwCol+'">'+rw+'</span>';
  if(!out) out = g;
  return out;
}

function _buildSanadChecklist(h) {
  /* Checklist mz-check-row pour les 5 conditions d'Ibn as-Salah */
  if (!h.sanad) return null;
  var s = h.sanad;
  var svgOk = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  var svgNo = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  var conds = [
    {fr:"AL-'ADALA \u2014 Probite du transmetteur",     ar:"\u0627\u0644\u0639\u064E\u062F\u064E\u0627\u0644\u064E\u0629", d:s.adala},
    {fr:"AD-DABT \u2014 Precision de la memorisation",   ar:"\u0627\u0644\u0636\u064E\u0628\u0652\u0637",               d:s.dabt},
    {fr:"AL-ITTISAL \u2014 Continuite de la chaine",     ar:"\u0627\u062A\u0651\u0650\u0635\u064E\u0627\u0644",          d:s.ittisal},
    {fr:"ASH-SHUDHUDH \u2014 Absence de contradiction",  ar:"\u0627\u0644\u0634\u064F\u0630\u064F\u0648\u0630",          d:s.shudhudh},
    {fr:"AL-'ILLAH \u2014 Absence de defaut cache",      ar:"\u0627\u0644\u0639\u0650\u0644\u0651\u064E\u0629",           d:s.illa}
  ];
  var html = '';
  conds.forEach(function(c){
    var st = c.d ? c.d.statut : 'na';
    var ok = (st==='sahih');
    var fail = (st==='daif'||st==='mafqud');
    var cls = ok ? 'pass' : (fail ? 'fail' : 'pass');
    var badge = ok ? 'REMPLIE' : (fail ? 'DEFAILLANTE' : 'NON EVALUEE');
    html += '<div class="mz-check-row">'
      +'<div class="mz-check-icon '+cls+'">'+(ok?svgOk:(fail?svgNo:svgOk))+'</div>'
      +'<div class="mz-check-texts">'
      +'<span class="mz-check-name '+cls+'">'+c.fr+'</span>'
      +'<span class="mz-check-ar">'+c.ar+'</span>'
      +(c.d&&c.d.detail?'<p class="mz-check-detail">'+c.d.detail+'</p>':'')
      +'</div>'
      +'<span class="mz-check-badge '+cls+'">'+badge+'</span>'
      +'</div>';
  });
  return html;
}

function _buildAnalyseText(h) {
  if (h.albani && h.albani.raisonnement) return h.albani.raisonnement;
  return h.fr || '';
}

function _buildAvisSavants(h) {
  if (!h.albani || !h.albani.imams_cites || !h.albani.imams_cites.length) return [];
  return h.albani.imams_cites.map(function(ic) {
    return { savant: ic.imam.nom + ' — ' + ic.imam.epoque, citation: ic.jugement };
  });
}

/* ════════════════════════════════════════════════════════════════════
   § 6 — API PUBLIQUE window.MizanDB
════════════════════════════════════════════════════════════════════ */

window.MizanDB = {
  version      : MIZAN_DB_VERSION,
  load         : loadHadithDatabase,
  search       : searchHadith,
  searchForApp : searchHadithForApp,
  getByGrade   : function(grade, limit) {
    var idxs = _gradeIndex[grade.toUpperCase()] || [];
    return idxs.slice(0, limit||10).map(function(i){ return HADITH_DATABASE[i]; });
  },
  getById      : function(id) {
    for(var i=0;i<HADITH_DATABASE.length;i++){ if(HADITH_DATABASE[i].id===id) return HADITH_DATABASE[i]; }
    return null;
  },
  getStats     : function() {
    var s = { total: HADITH_DATABASE.length };
    Object.keys(_gradeIndex).forEach(function(g){ s[g] = _gradeIndex[g].length; });
    return s;
  },
  isLoaded     : function() { return MIZAN_DB_LOADED; },
  getImams     : function() { return IMAMS; },
  getOuvrages  : function() { return OUVRAGES_ALBANI; }
};



/* ════════════════════════════════════════

/* ══════════════════════════════════════════════════════════════
   Confirmation de chargement
══════════════════════════════════════════════════════════════ */
window.MizanDB.load(function() {
  console.log('%c ✅ Mîzân v18.4 — db.js : MizanDB chargé — ' + window.MizanDB.getStats().total + ' hadiths indexés', 'color:#22c55e;font-weight:bold;');
});
