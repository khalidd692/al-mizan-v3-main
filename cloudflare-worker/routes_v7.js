/**
 * Cloudflare Worker — AL-MĪZĀN V7.0
 * Routes complètes avec Lexique de Fer
 */

// ============================================================
// CONFIGURATION
// ============================================================

const CLAUDE_API_KEY = CLAUDE_API_KEY_ENV; // Variable d'environnement
const FAWAZ_CDN_BASE = 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1';
const HADEETHENC_BASE = 'https://hadeethenc.com/api/v1';
const DORAR_API_BASE = 'http://localhost:5000/v1'; // À remplacer par URL production

// ============================================================
// LEXIQUE DE FER — Prompt Claude
// ============================================================

const LEXIQUE_FER_PROMPT = `Tu es un traducteur spécialisé dans les hadiths du Prophète Muhammad ﷺ.
Tu traduis UNIQUEMENT du texte arabe vers le français.

RÈGLES ABSOLUES — LEXIQUE DE FER :
1. استوى → "S'est établi" (jamais d'autre formulation)
2. يد الله / يده → "la Main d'Allah" / "Sa Main" (littéral uniquement)
3. وجه الله / وجهه → "la Face d'Allah" / "Sa Face" (littéral uniquement)
4. نزل / ينزل → "descend" / "descendra" (jamais "se manifeste")
5. فوق / العلو → "au-dessus" / "l'élévation" (jamais "au-delà" ou métaphore)
6. الرحمة → "la Miséricorde" (si attribut d'Allah), "la miséricorde" (si autre)
7. الغضب → "la Colère" (si attribut d'Allah, littéral, sans ta'wîl)
8. المحبة / الحب → "l'Amour" (si attribut d'Allah, littéral)

INTERDICTIONS :
- Aucune explication ou commentaire dans la traduction
- Aucun ajout entre parenthèses pour "expliquer" les attributs
- Aucun ta'wîl (réinterprétation) des attributs d'Allah
- Aucune traduction par "puissance", "essence", "grâce" à la place d'attributs littéraux

STYLE :
- Traduction claire, lisible en français moderne
- Conserver le style solennel des hadiths
- Noms propres arabes en translittération standard islamique

Traduis maintenant ce hadith en français en respectant ces règles :`;

// ============================================================
// ROUTE A : Traduction FR → mots-clés AR (existante)
// ============================================================

async function handleTranslateFrToAr(request) {
  const { query } = await request.json();
  
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 100,
      messages: [{
        role: 'user',
        content: `Extrais 2-3 mots-clés arabes pour rechercher des hadiths sur: "${query}". Réponds UNIQUEMENT avec les mots arabes séparés par des espaces, sans explication.`
      }]
    })
  });
  
  const data = await response.json();
  const keywords = data.content[0].text.trim().split(/\s+/);
  
  return new Response(JSON.stringify({ keywords }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

// ============================================================
// ROUTE B : Recherche Dorar (existante, améliorée)
// ============================================================

async function handleSearchDorar(request) {
  const url = new URL(request.url);
  const q = url.searchParams.get('q');
  const grade = url.searchParams.get('grade') || 'sahih';
  const book = url.searchParams.get('book');
  
  // Construire les paramètres Dorar
  const params = new URLSearchParams({
    value: q,
    removeHTML: 'true',
    specialist: '0'
  });
  
  // Grades
  if (grade === 'sahih') {
    params.append('d[]', '1'); // Sahih
    params.append('d[]', '2'); // Sahih li ghayrih
  }
  
  // Livres
  if (book === 'bukhari') params.append('s[]', '6216');
  if (book === 'muslim') params.append('s[]', '3088');
  
  const dorarUrl = `${DORAR_API_BASE}/api/hadith/search?${params}`;
  
  const response = await fetch(dorarUrl);
  const data = await response.json();
  
  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json' }
  });
}

// ============================================================
// ROUTE C : Traduction AR → FR avec Lexique de Fer (existante)
// ============================================================

async function handleTranslateHadith(request) {
  const { ar_text } = await request.json();
  
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': CLAUDE_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-3-haiku-20240307',
      max_tokens: 1000,
      temperature: 0.3,
      system: LEXIQUE_FER_PROMPT,
      messages: [{
        role: 'user',
        content: ar_text
      }]
    })
  });
  
  const data = await response.json();
  const fr_text = data.content[0].text.trim();
  
  // Vérification anti-ta'wîl
  const termes_interdits = ['puissance', 'essence', 'se manifeste', 'au-delà'];
  const violations = termes_interdits.filter(t => fr_text.toLowerCase().includes(t));
  
  if (violations.length > 0) {
    console.warn('⚠️ Violations Lexique de Fer détectées:', violations);
  }
  
  return new Response(JSON.stringify({ 
    fr_text,
    lexique_fer_applied: true,
    violations: violations.length > 0 ? violations : null
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

// ============================================================
// ROUTE D : NOUVELLE — Récupération traduction FR directe
// ============================================================

async function handleFetchFrDirect(request) {
  const url = new URL(request.url);
  const livre = url.searchParams.get('livre'); // bukhari, muslim, etc.
  const numero = url.searchParams.get('numero');
  
  const livreMap = {
    'bukhari': 'fra-bukhari',
    'muslim': 'fra-muslim',
    'abudawud': 'fra-abudawud',
    'ibnmajah': 'fra-ibnmajah',
    'malik': 'fra-malik',
    'dehlawi': 'fra-dehlawi',
    'nawawi': 'fra-nawawi'
  };
  
  const livreCode = livreMap[livre];
  if (!livreCode) {
    return new Response(JSON.stringify({ error: 'Livre non supporté' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  const fawazUrl = `${FAWAZ_CDN_BASE}/editions/${livreCode}/${numero}.json`;
  
  try {
    const response = await fetch(fawazUrl);
    if (response.status === 200) {
      const data = await response.json();
      return new Response(JSON.stringify({
        id: `fawaz-${livre}-${numero}`,
        fr_text: data.text || data.hadith,
        fr_source: 'fawazahmed0',
        source_url: fawazUrl,
        source_version_pin: '@1',
        hadith_number: numero,
        book_name_fr: livre
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } else if (response.status === 404) {
      return new Response(JSON.stringify({ error: 'Hadith non trouvé' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// ============================================================
// ROUTE E : NOUVELLE — Explication HadeethEnc
// ============================================================

async function handleFetchExplanation(request) {
  const url = new URL(request.url);
  const id = url.searchParams.get('id');
  const lang = url.searchParams.get('lang') || 'fr';
  
  const hadeethencUrl = `${HADEETHENC_BASE}/hadeeths/one/?id=${id}&language=${lang}`;
  
  try {
    const response = await fetch(hadeethencUrl);
    if (response.status === 200) {
      const data = await response.json();
      return new Response(JSON.stringify({
        id: `hadeethenc-${id}`,
        fr_text: data.hadeeth,
        fr_explanation: data.explanation,
        fr_summary: data.title,
        fr_source: 'hadeethenc',
        source_url: `https://hadeethenc.com/fr/browse/hadith/${id}`,
        attribution: data.attribution,
        hints: data.hints,
        categories: data.categories,
        conditions: [
          'Aucune modification du contenu',
          'Référence obligatoire à HadeethEnc.com',
          'Usage commercial interdit sans autorisation'
        ]
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } else if (response.status === 404) {
      return new Response(JSON.stringify({ error: 'Hadith non trouvé' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// ============================================================
// ROUTE F : NOUVELLE — Sharh Dorar
// ============================================================

async function handleFetchSharh(request) {
  const url = new URL(request.url);
  const hadithId = url.searchParams.get('hadith_id');
  
  const dorarUrl = `${DORAR_API_BASE}/api/hadith/${hadithId}/sharh`;
  
  try {
    const response = await fetch(dorarUrl);
    if (response.status === 200) {
      const data = await response.json();
      return new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      throw new Error(`HTTP ${response.status}`);
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// ============================================================
// ROUTER PRINCIPAL
// ============================================================

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  };
  
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }
  
  let response;
  
  try {
    // Routes existantes
    if (path === '/translate' && request.method === 'POST') {
      response = await handleTranslateFrToAr(request);
    } else if (path === '/search') {
      response = await handleSearchDorar(request);
    } else if (path === '/translate-hadith' && request.method === 'POST') {
      response = await handleTranslateHadith(request);
    }
    // Nouvelles routes V7
    else if (path === '/fra') {
      response = await handleFetchFrDirect(request);
    } else if (path === '/explanation') {
      response = await handleFetchExplanation(request);
    } else if (path === '/sharh') {
      response = await handleFetchSharh(request);
    }
    // Route par défaut
    else {
      response = new Response(JSON.stringify({
        name: 'AL-MĪZĀN V7.0 API',
        routes: {
          'POST /translate': 'Traduire FR → mots-clés AR',
          'GET /search': 'Rechercher dans Dorar',
          'POST /translate-hadith': 'Traduire AR → FR (Lexique de Fer)',
          'GET /fra': 'Récupérer hadith FR direct (fawazahmed0)',
          'GET /explanation': 'Récupérer explication (HadeethEnc)',
          'GET /sharh': 'Récupérer sharh (Dorar)'
        }
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Ajouter CORS headers à la réponse
    const newHeaders = new Headers(response.headers);
    Object.entries(corsHeaders).forEach(([key, value]) => {
      newHeaders.set(key, value);
    });
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}