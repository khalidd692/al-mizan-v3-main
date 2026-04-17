/* ═══════════════════════════════════════════════════════════════════
   MÎZÂN v18.4 — faq.js
   Rôle    : Données FAQ + rendu (Kashf ash-Shubuhat)
   Contenu : FAQ_OPEN_ID · FAQ[] · renderFAQ() · toggleFAQ()
   Sources : binbaz.org.sa · alalbany.net · binothaimeen.net
═══════════════════════════════════════════════════════════════════ */

var FAQ_OPEN_ID = null;

var FAQ = [
  // ══════════════════════════════════════════════════════════════
  // KASHF ASH-SHUBUHAT — LES 7 AMBIGUÏTÉS MAJEURES
  // ══════════════════════════════════════════════════════════════
  {id:101,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Mettre en garde, n'est-ce pas de la médisance (Ghibah) interdite ? »",
   a:"NON. L'Imam An-Nawawi (رحمه الله) dans Riyad As-Salihin a listé 6 cas où la médisance est AUTORISÉE et même OBLIGATOIRE. Parmi eux : 'At-Tahdhir wal-Intibah' — la mise en garde et l'alerte pour protéger la communauté contre un mal. Mettre en garde contre un prédicateur déviant rentre précisément dans ce cas. Ce n'est pas de la Ghibah — c'est de la Nassiha (conseil sincère) et du Dhabb 'an as-Sunnah (défense de la Sunnah). L'Imam Ahmad a dit : 'Si tu te tais et que je me tais, qui informera l'ignorant du savant et du menteur ?'",
   dalil:"L'Imam An-Nawawi (رحمه الله) — Riyad As-Salihin — Chapitre sur les 6 cas de médisance autorisée : (1) L'opprimé qui se plaint, (2) La demande de fatwa, (3) La mise en garde contre le mal (التحذير), (4) Le pécheur public, (5) L'identification d'une personne connue par un surnom, (6) Celui qui pratique l'innovation ouvertement. La mise en garde contre un prédicateur déviant entre dans les cas 3, 4 et 6. Cheikh Ibn Baz (binbaz.org.sa) : 'Mettre en garde contre les innovateurs est une obligation, pas de la Ghibah — c'est protéger la religion d'Allah.'",
   verdict:"OBLIGATION RELIGIEUSE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  {id:102,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Pourquoi ne pas les conseiller en privé d'abord ? »",
   a:"Le conseil en privé est la règle pour le PÉCHEUR qui cache son péché. Mais celui qui propage l'innovation PUBLIQUEMENT — via YouTube, TikTok, mosquées, conférences — doit être réfuté PUBLIQUEMENT. C'est le principe unanime des Salaf : 'من جاهر بالبدعة فقد أسقط حرمته' — Celui qui affiche son innovation a perdu sa protection. Le Prophète ﷺ lui-même nommait les gens publiquement quand c'était nécessaire : 'Qu'en est-il de gens qui stipulent des conditions qui ne sont pas dans le Livre d'Allah ?' (Bukhari n°456).",
   dalil:"Cheikh Salih Al-Fawzan (alfawzan.af.org.sa) : 'Le pécheur en privé se conseille en privé. Mais celui qui propage sa déviance publiquement — dans les mosquées, sur Internet, dans les médias — sa réfutation est publique, car le mal est public.' Cheikh Al-Albani (alalbany.net) : 'Les Salaf réfutaient les innovateurs par leurs noms — ce n'est pas de la médisance mais de la protection de la religion.' Le Prophète ﷺ dans Bukhari n°456 a nommé des gens publiquement pour protéger la communauté.",
   verdict:"RÉFUTATION PUBLIQUE OBLIGATOIRE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  {id:103,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Seul Allah juge — qui êtes-vous pour juger les gens ? »",
   a:"Cette phrase détourne un verset de son sens pour paralyser la religion. Allah a ORDONNÉ aux croyants de juger par le visible (Dhahir) : 'Ordonnez le bien et interdisez le mal' (Coran 3:110). Le Prophète ﷺ a dit : 'Celui d'entre vous qui voit un mal, qu'il le change avec sa main ; s'il ne peut pas, avec sa langue ; s'il ne peut pas, avec son cœur — et c'est le plus faible degré de la foi.' (Muslim n°49). Juger les ACTES et les PAROLES publiques n'est pas juger le cœur — c'est une obligation.",
   dalil:"Coran 3:110 — 'Vous êtes la meilleure communauté suscitée pour les hommes : vous ordonnez le bien et interdisez le mal.' Muslim n°49 — Hadith du changement du mal. Cheikh Ibn 'Uthaymin (binothaimeen.net) : 'Nous ne jugeons pas le cœur des gens — c'est pour Allah. Mais nous jugeons ce qui est apparent : les paroles, les actes et la méthodologie. C'est obligatoire.' Cheikh Rabi' (rabee.net) : 'Dire Seul Allah juge pour empêcher le Jarh wa Ta'dil, c'est annuler une science entière des Salaf.'",
   verdict:"OBLIGATION CORANIQUE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  {id:104,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Pourquoi citez-vous les noms publiquement ? »",
   a:"Parce que les Salaf as-Salih l'ont fait avant nous. Yahya ibn Ma'in, Al-Bukhari, Muslim, Abu Hatim Ar-Razi — ils ont TOUS nommé publiquement les narrateurs faibles, les menteurs et les innovateurs. C'est la méthode de toute la science du Jarh wa Ta'dil depuis 14 siècles. Cacher le nom d'un déviant tout en mettant en garde revient à ne pas mettre en garde du tout — le mal continue de se propager sans que les gens sachent de qui se protéger.",
   dalil:"Imam Muslim dans l'introduction de son Sahih cite Muhammad ibn Sirin (رحمه الله) : 'Nommez-nous vos hommes.' L'Imam Al-Bukhari a compilé 'Ad-Du'afa as-Saghir' — le livre des narrateurs NOMMÉS et critiqués. Cheikh Al-Albani (alalbany.net) : 'Les savants du Jarh wa Ta'dil ont toujours nommé les gens — c'est la seule manière efficace de protéger la communauté. Celui qui dit le contraire détruit la science du Hadith elle-même.'",
   verdict:"MÉTHODE DES SALAF",verdictColor:"#c9a84c",verdictBg:"rgba(201,168,76,.1)"},

  {id:105,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Vous êtes des Madkhalistes — vous suivez un seul homme ! »",
   a:"Le terme 'Madkhaliste' est une étiquette inventée par les innovateurs pour repousser la vérité — exactement comme les anciens innovateurs appelaient les Ahl al-Hadith 'Hashawiyyah' (marginaux). La science du Jarh wa Ta'dil n'est pas l'invention de Cheikh Rabi' — elle est pratiquée par les 4 Imams, Yahya ibn Ma'in, Al-Bukhari, Muslim, et 12 montagnes de l'Islam sur 14 siècles. Cheikh Rabi' a été recommandé par l'Imam Al-Albani ('porte-étendard du Jarh'), l'Imam Ibn Baz, l'Imam Ibn 'Uthaymin, Cheikh Al-Fawzan et Cheikh Muqbil. Ce n'est pas un homme — c'est un consensus.",
   dalil:"L'Imam Al-Barbahari (رحمه الله) dans Sharh As-Sunnah : 'Quand tu entends un homme dire Untel est un Hashawi, sache que c'est un innovateur.' L'Imam Al-Albani : 'حامل راية الجرح والتعديل في هذا العصر هو الشيخ ربيع' — Le porte-étendard du Jarh wa Ta'dil à notre époque est Cheikh Rabi'. [Enregistrement authentifié]. Cheikh Ibn Baz, Cheikh Al-Fawzan et la Lajnah Da'imah ont tous soutenu sa méthode.",
   verdict:"ÉTIQUETTE SECTAIRE REJETÉE",verdictColor:"#991b1b",verdictBg:"rgba(153,27,27,.1)"},

  {id:106,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Ces prédicateurs font du bien — pourquoi ne pas prendre le bon et laisser le mal ? »",
   a:"L'Imam Malik (رحمه الله) a interdit de prendre la science de 4 catégories de personnes — parmi elles le partisan de la passion (sahib hawa). La règle des Salaf : on ne boit pas d'eau polluée même si 90% de l'eau est pure. Le poison de l'innovation est plus dangereux que le poison du corps. Cheikh Al-Fawzan : 'Celui qui mélange le vrai et le faux est plus dangereux que le faux pur — car il trompe les gens.'",
   dalil:"L'Imam Malik — rapporté par Al-Khatib Al-Baghdadi : 'لا يُؤخذ العلم من صاحب هوى يدعو إليه' — On ne prend pas la science du partisan de la passion. Cheikh Rabi' (rabee.net) : 'Le Mumayyi' (celui qui mélange) est plus dangereux que le Mubtadi' (innovateur) déclaré — car le Mumayyi' rend le poison buvable.' Cheikh Ibn 'Uthaymin (binothaimeen.net) : 'Le serpent le plus dangereux est celui qui se cache dans l'herbe verte.'",
   verdict:"INTERDIT PAR LES SALAF",verdictColor:"#ef4444",verdictBg:"rgba(239,68,68,.1)"},

  {id:107,cat:"Shubuhât — Ambiguïtés",icon:"◼",iconBg:"rgba(153,27,27,.1)",iconColor:"#991b1b",
   q:"« Vous créez la division (Fitna) dans la Oumma ! »",
   a:"C'est l'INNOVATION qui crée la division — pas la réfutation de l'innovation. Le Prophète ﷺ a annoncé que sa Oumma se diviserait en 73 sectes (At-Tirmidhi, authentifié). La division existe déjà — la question est : es-tu du côté des 72 sectes ou de la seule sauvée ? Les Salaf qui réfutaient les innovateurs ne créaient pas la division — ils protégeaient l'unité sur la VÉRITÉ. L'unité sur le faux n'a aucune valeur en Islam.",
   dalil:"Hadith des 73 sectes (At-Tirmidhi, authentifié par Al-Albani) : 'Ma Oumma se divisera en 73 groupes — tous en Enfer sauf un.' Cheikh Ibn Baz (binbaz.org.sa) : 'L'unité recherchée en Islam est l'unité sur la vérité (Al-Haqq) — pas l'unité sur le mensonge. Se réunir avec les innovateurs n'est pas de l'unité, c'est de la complicité dans l'égarement.' Cheikh Al-Albani : 'C'est l'innovation qui divise — la Sunnah unifie.'",
   verdict:"L'INNOVATION DIVISE — LA SUNNAH UNIFIE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  // ══════════════════════════════════════════════════════════════
  // QUESTIONS PRATIQUES (Masâ'il 'Amaliyyah)
  // ══════════════════════════════════════════════════════════════
  {id:1,cat:"Masâjid — Mosquées",icon:"◻",iconBg:"rgba(201,168,76,.1)",iconColor:"#c9a84c",
   q:"Est-ce que je peux aller dans la mosquée d'un prédicateur déviant ?",
   a:"Si tu as la possibilité d'aller ailleurs, il vaut mieux éviter la mosquée d'un prédicateur réfuté. Si c'est la seule mosquée disponible, tu peux y faire la salat sans écouter le khutbah de quelqu'un de déviant.",
   dalil:"Cheikh Al-Albani a dit : 'Fuis les innovateurs car leur compagnie est une maladie pour le cœur.' La fréquentation régulière affecte progressivement la pensée.",
   verdict:"ÉVITER si possible",verdictColor:"#f59e0b",verdictBg:"rgba(245,158,11,.1)"},

  {id:2,cat:"Masâjid — Mosquées",icon:"◻",iconBg:"rgba(201,168,76,.1)",iconColor:"#c9a84c",
   q:"Est-ce que je peux écouter les cours d'un prédicateur À ÉVITER sur YouTube ?",
   a:"Non, et surtout pas sans science islamique solide pour filtrer les erreurs. Un prédicateur classé À ÉVITER ou DANGER diffuse des déviations parfois subtiles. Sans formation, tu risques d'intégrer des erreurs sans t'en rendre compte.",
   dalil:"Ibn Sirine disait : 'Cette science est la religion — faites attention à qui vous prenez votre religion.' (Muslim, introduction). Le canal YouTube n'enlève pas la responsabilité.",
   verdict:"À ÉVITER",verdictColor:"#ef4444",verdictBg:"rgba(239,68,68,.1)"},

  {id:3,cat:"Mu'âmalât — Relations",icon:"◻",iconBg:"rgba(99,102,241,.1)",iconColor:"#818cf8",
   q:"Mon ami défend un prédicateur réfuté. Comment lui en parler ?",
   a:"Commence par l'écouter, comprends pourquoi il l'apprécie. Ensuite présente les preuves documentées — pas des opinions. Consulte les fiches des prédicateurs dans Al Mizan pour y trouver les paroles des savants et les preuves adaptées. La douceur est obligatoire, la clarté aussi.",
   dalil:"Le Prophète ﷺ a dit : 'La religion c'est le conseil sincère.' (Muslim n°55). Conseiller quelqu'un qui suit un déviant c'est de la nasiha, pas de la ghibah.",
   verdict:"NASIHA DOUCE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  {id:4,cat:"Mu'âmalât — Relations",icon:"◻",iconBg:"rgba(99,102,241,.1)",iconColor:"#818cf8",
   q:"Est-ce que critiquer un prédicateur c'est de la médisance (ghibah) ?",
   a:"Non. Les savants ont clairement établi que mettre en garde contre un prédicateur déviant est une obligation, pas de la ghibah. C'est de la nasiha — un conseil sincère pour protéger la communauté. Al-Albani, Ibn Baz et Rabi ont tous pratiqué le Jarh wa Ta'dil publiquement.",
   dalil:"Imam Ahmad a dit : 'Si tu te tais et que je me tais, qui informera l'ignorant ?' Al-Albani : 'Critiquer l'innovateur n'est pas de la ghibah — c'est protéger la religion.'",
   verdict:"OBLIGATOIRE",verdictColor:"#22c55e",verdictBg:"rgba(34,197,94,.1)"},

  {id:5,cat:"Mu'âmalât — Relations",icon:"◻",iconBg:"rgba(99,102,241,.1)",iconColor:"#818cf8",
   q:"Ma famille suit un prédicateur déviant. Que faire ?",
   a:"Patience et sagesse. Ne romps pas les liens familiaux. Commence par partager des contenus de savants fiables sans mentionner explicitement ce que tu penses de leur prédicateur. Avec le temps et la douceur, le cœur change. Le boycott brutal produit l'effet inverse.",
   dalil:"Cheikh Rabi a rappelé que la da'wah dans la famille nécessite de la hikmah (sagesse). L'objectif est de les guider, pas de gagner un débat.",
   verdict:"HIKMAH",verdictColor:"#a78bfa",verdictBg:"rgba(167,139,250,.1)"},

  {id:6,cat:"'Aqida wal-Manhaj",icon:"◻",iconBg:"rgba(245,158,11,.1)",iconColor:"#f59e0b",
   q:"Comment savoir si un prédicateur est vraiment fiable ?",
   a:"4 critères selon le Jarh wa Ta'dil : 1) Son aqida est-elle conforme aux Salaf sur les attributs d'Allah ? 2) A-t-il une tazkiya nominative d'un grand savant reconnu ? 3) Se positionne-t-il clairement contre les groupes déviants ? 4) Qui sont ses maîtres ?",
   dalil:"Cheikh Rabi : 'Le prédicateur doit avoir une aqida correcte, un manhaj salafi, et une recommandation de savants reconnus. Sans ces 3 éléments, la prudence s'impose.'",
   verdict:"4 CRITÈRES CLÉS",verdictColor:"#c9a84c",verdictBg:"rgba(201,168,76,.1)"},

  {id:7,cat:"'Aqida wal-Manhaj",icon:"◻",iconBg:"rgba(245,158,11,.1)",iconColor:"#f59e0b",
   q:"Un prédicateur réfuté peut-il se repentir et redevenir fiable ?",
   a:"Oui, mais le repentir doit être public, documenté, et validé par les savants qui l'avaient réfuté. Une simple disparition des réseaux ou un changement de discours ne suffit pas. Les savants doivent confirmer le retour à la vérité.",
   dalil:"Cheikh Rabi a dit que le repentir d'un innovateur se prouve par une rétractation claire et publique des erreurs passées, confirmée par les savants du Jarh wa Ta'dil.",
   verdict:"PREUVE REQUISE",verdictColor:"#f59e0b",verdictBg:"rgba(245,158,11,.1)"},

  {id:8,cat:"'Aqida wal-Manhaj",icon:"◻",iconBg:"rgba(245,158,11,.1)",iconColor:"#f59e0b",
   q:"C'est quoi la différence entre un Frère Musulman et un Salafi ?",
   a:"Méthode radicalement différente. Les Frères Musulmans : politique avant aqida, unité avec les déviants, travail dans les partis. Les Salafis : aqida et purification de la croyance d'abord, aucune alliance avec les innovateurs, obéissance aux dirigeants dans le bien.",
   dalil:"Cheikh Rabi : 'Les Frères Musulmans ont sacrifié l'aqida sur l'autel de la politique. Les Salafis suivent la voie du Prophète ﷺ : purifier la croyance en premier.'",
   verdict:"DISTINCTION CLEF",verdictColor:"#a78bfa",verdictBg:"rgba(167,139,250,.1)"},

  {id:9,cat:"Al-Wâqi' — Contexte français",icon:"◻",iconBg:"rgba(59,130,246,.1)",iconColor:"#60a5fa",
   q:"Quels sont les réseaux fréristes présents en France ?",
   a:"Les principaux : UOIF (rebaptisée Musulmans de France), Collectif Contre l'Islamophobie (CCIF dissous), certaines mosquées rattachées aux Frères, certaines écoles islamiques, et de nombreux comptes YouTube/Instagram qui diffusent leur idéologie sans le dire explicitement.",
   dalil:"Cheikh Rabi a mis en garde spécifiquement contre les Frères Musulmans en Europe : 'Ils contrôlent les associations, les mosquées et les médias musulmans dans vos pays.'",
   verdict:"VIGILANCE",verdictColor:"#ef4444",verdictBg:"rgba(239,68,68,.1)"},

  {id:10,cat:"Al-Wâqi' — Contexte français",icon:"◻",iconBg:"rgba(59,130,246,.1)",iconColor:"#60a5fa",
   q:"Puis-je me fier aux instituts islamiques en France pour apprendre ?",
   a:"Ça dépend de l'institut. Beaucoup d'instituts francophones sont proches des Ash'arites ou des Frères Musulmans. Avant de t'inscrire, vérifie qui sont les enseignants et quel est leur manhaj. Préfère les cours en ligne de savants salafis reconnus comme source principale.",
   dalil:"Ibn Sirine : 'Cette science est la religion — faites attention à qui vous prenez votre religion.' S'inscrire dans un institut c'est choisir un chemin — vérifie où il mène.",
   verdict:"VÉRIFIER D'ABORD",verdictColor:"#f59e0b",verdictBg:"rgba(245,158,11,.1)"}
];

function renderFAQ(){
  var q = (document.getElementById('faq-search') ? document.getElementById('faq-search').value : '').toLowerCase().trim();
  var results = FAQ.filter(function(f){
    if(!q) return true;
    return f.q.toLowerCase().indexOf(q)!==-1 || f.a.toLowerCase().indexOf(q)!==-1 || f.cat.toLowerCase().indexOf(q)!==-1;
  });

  var cats = {};
  results.forEach(function(f){
    if(!cats[f.cat]) cats[f.cat]=[];
    cats[f.cat].push(f);
  });

  /* ── BOUCLIER SYNTAXE : createElement / textContent exclusivement ── */
  var list = document.getElementById('faq-list');
  if (!list) return;
  while (list.firstChild) list.removeChild(list.firstChild);

  var catKeys = Object.keys(cats);

  if (!catKeys.length) {
    var empty = document.createElement('div');
    empty.style.cssText = 'text-align:center;padding:40px 20px;font-family:Cormorant Garamond,serif;font-style:italic;color:rgba(201,168,76,.3);font-size:14px;';
    empty.textContent = 'Aucune question trouvée';
    list.appendChild(empty);
    return;
  }

  catKeys.forEach(function(cat) {
    /* Titre catégorie */
    var catTitle = document.createElement('div');
    catTitle.className = 'faq-category-title';
    catTitle.textContent = cat.toUpperCase();
    list.appendChild(catTitle);

    cats[cat].forEach(function(f, i) {
      var isOpen = FAQ_OPEN_ID === f.id;

      /* Item wrapper */
      var item = document.createElement('div');
      item.className = 'faq-item' + (isOpen ? ' open' : '');
      item.id = 'faqitem-' + f.id;
      item.style.cssText = 'animation:argCardIn .35s ease both;animation-delay:' + (i * 0.05) + 's;';
      item.addEventListener('click', (function(fid) {
        return function() { window.toggleFAQ(fid); };
      })(f.id));

      /* Head */
      var head = document.createElement('div');
      head.className = 'faq-item-head';

      var icon = document.createElement('div');
      icon.className = 'faq-q-icon';
      icon.style.cssText = 'background:' + f.iconBg + ';color:' + f.iconColor + ';';
      icon.textContent = f.icon;

      var qText = document.createElement('span');
      qText.className = 'faq-q-text';
      qText.textContent = f.q;

      var arrow = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      arrow.setAttribute('class', 'faq-arrow');
      arrow.setAttribute('viewBox', '0 0 24 24');
      arrow.setAttribute('fill', 'none');
      arrow.setAttribute('stroke', 'currentColor');
      arrow.setAttribute('stroke-width', '2');
      arrow.setAttribute('stroke-linecap', 'round');
      arrow.setAttribute('stroke-linejoin', 'round');
      var polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      polyline.setAttribute('points', '6 9 12 15 18 9');
      arrow.appendChild(polyline);

      head.appendChild(icon);
      head.appendChild(qText);
      head.appendChild(arrow);

      /* Body */
      var body = document.createElement('div');
      body.className = 'faq-body';

      var answer = document.createElement('div');
      answer.className = 'faq-answer';

      var answerText = document.createElement('p');
      answerText.className = 'faq-answer-text';
      answerText.textContent = f.a;

      var dalilBox = document.createElement('div');
      dalilBox.className = 'faq-dalil';
      var dalilLabel = document.createElement('span');
      dalilLabel.className = 'faq-dalil-label';
      dalilLabel.textContent = 'PREUVE — DALIL';
      var dalilText = document.createElement('p');
      dalilText.textContent = f.dalil;
      dalilBox.appendChild(dalilLabel);
      dalilBox.appendChild(dalilText);

      var verdict = document.createElement('span');
      verdict.className = 'faq-verdict';
      verdict.style.cssText = 'background:' + f.verdictBg + ';border:1px solid ' + f.verdictColor + '44;color:' + f.verdictColor + ';';
      verdict.textContent = f.verdict;

      answer.appendChild(answerText);
      answer.appendChild(dalilBox);
      answer.appendChild(verdict);
      body.appendChild(answer);

      item.appendChild(head);
      item.appendChild(body);
      list.appendChild(item);
    });
  });
}
window.toggleFAQ = function(id) {
  FAQ_OPEN_ID = (FAQ_OPEN_ID === id) ? null : id;
  renderFAQ();
};
window.renderFAQ = renderFAQ;


console.log('%c ✅ Mîzân v18.4 — faq.js : FAQ (' + FAQ.length + ' questions) chargé', 'color:#f472b6;font-weight:bold;');
