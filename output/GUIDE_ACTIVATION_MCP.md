# 🔌 GUIDE D'ACTIVATION DES EXTENSIONS MCP

## 📋 EXTENSIONS MCP DISPONIBLES

Al-Mīzān v7.0 peut utiliser les extensions MCP suivantes pour le scraping réel :

### 1. Tavily Search (Recherche intelligente)
- **Serveur:** `github.com/tavily-ai/tavily-mcp`
- **Usage:** Recherche de hadiths sur Dorar.net et autres sources
- **Avantages:** Recherche sémantique, filtrage par domaine

### 2. Browser MCP (Scraping web)
- **Serveur:** `github.com/BrowserMCP/mcp`
- **Usage:** Navigation et extraction de contenu depuis Dorar.net
- **Avantages:** Extraction HTML, snapshots, interaction avec pages

### 3. Playwright MCP (Alternative browser)
- **Serveur:** `github.com/microsoft/playwright-mcp`
- **Usage:** Scraping avancé avec Playwright
- **Avantages:** Plus robuste, gestion JavaScript

---

## 🚀 ACTIVATION ÉTAPE PAR ÉTAPE

### Étape 1: Vérifier les extensions disponibles

Les extensions MCP sont déjà configurées dans votre environnement Kiro. Vérifiez qu'elles sont actives :

```bash
# Vérifier Tavily
# L'extension devrait être listée dans les MCP servers disponibles

# Vérifier Browser
# L'extension devrait être listée dans les MCP servers disponibles
```

### Étape 2: Tester Tavily Search

```python
# Test de recherche Tavily
# Cette commande sera exécutée via use_mcp_tool

query = "site:dorar.net صحيح البخاري"
results = await use_mcp_tool("tavily_search", {
    "query": query,
    "max_results": 10,
    "include_domains": ["dorar.net"]
})
```

### Étape 3: Tester Browser MCP

```python
# Test de navigation browser
# Cette commande sera exécutée via use_mcp_tool

url = "https://dorar.net/hadith/search?skey=6216&page=1"
await use_mcp_tool("browser_navigate", {"url": url})
snapshot = await use_mcp_tool("browser_snapshot", {})
```

---

## 🔧 INTÉGRATION DANS LE CONNECTEUR

### Modification du DorarConnectorMCP

Pour activer le scraping réel, modifier `backend/connectors/dorar_connector_mcp.py` :

```python
async def _fetch_with_mcp(self, url: str, hadith_id: int, book_key: str) -> Optional[Dict]:
    """
    Extraction réelle avec MCP Browser
    """
    self.session_stats["mcp_calls"] += 1
    
    try:
        # 1. Navigation vers la page
        await use_mcp_tool("browser_navigate", {"url": url})
        
        # 2. Attendre le chargement
        await use_mcp_tool("browser_wait", {"time": 2})
        
        # 3. Capturer le contenu
        snapshot = await use_mcp_tool("browser_snapshot", {})
        
        # 4. Parser le HTML pour extraire les données
        hadith_data = self._parse_dorar_html(snapshot)
        
        return hadith_data
        
    except Exception as e:
        print(f"❌ Erreur MCP: {e}")
        return None
```

### Fonction de parsing HTML

```python
def _parse_dorar_html(self, html_content: str) -> Dict:
    """
    Parse le HTML de Dorar pour extraire les données du hadith
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extraire le matn (texte du hadith)
    matn_elem = soup.find('div', class_='hadith-text')
    matn = matn_elem.text.strip() if matn_elem else ""
    
    # Extraire le narrateur
    rawi_elem = soup.find('div', class_='hadith-narrator')
    rawi = rawi_elem.text.strip() if rawi_elem else ""
    
    # Extraire le grade
    grade_elem = soup.find('span', class_='grade')
    grade = grade_elem.text.strip() if grade_elem else "unknown"
    
    # Extraire le muhaddith
    muhaddith_elem = soup.find('span', class_='muhaddith')
    muhaddith = muhaddith_elem.text.strip() if muhaddith_elem else ""
    
    return {
        "matn": matn,
        "rawi": rawi,
        "grade": grade,
        "graded_by": muhaddith,
        # ... autres champs
    }
```

---

## 📊 UTILISATION EN PRODUCTION

### Lancer avec MCP activé

```bash
# Mode MCP réel (scraping Dorar.net)
python backend/production_harvester.py --book bukhari --mcp

# Mode simulation (pour tests)
python backend/production_harvester.py --book bukhari
```

### Avantages du mode MCP

1. **Données réelles** depuis Dorar.net
2. **Grades authentiques** validés par les Muhaddithin
3. **Textes complets** en arabe
4. **Métadonnées complètes** (takhrij, sharh, etc.)

### Inconvénients à considérer

1. **Plus lent** (rate limiting nécessaire)
2. **Dépendant** de la disponibilité de Dorar.net
3. **Parsing HTML** peut nécessiter des ajustements

---

## 🔍 RECHERCHE INTELLIGENTE AVEC TAVILY

### Cas d'usage

Tavily est utile pour :
- Trouver des hadiths par thème
- Rechercher des variantes
- Découvrir des sources alternatives

### Exemple d'utilisation

```python
async def search_hadith_by_theme(self, theme: str) -> List[Dict]:
    """
    Recherche de hadiths par thème avec Tavily
    """
    query = f"site:dorar.net {theme} حديث"
    
    results = await use_mcp_tool("tavily_search", {
        "query": query,
        "max_results": 20,
        "include_domains": ["dorar.net"],
        "search_depth": "advanced"
    })
    
    # Parser les résultats
    hadiths = []
    for result in results:
        url = result.get("url")
        # Extraire l'ID du hadith depuis l'URL
        hadith_id = self._extract_hadith_id_from_url(url)
        if hadith_id:
            hadith = await self.fetch_hadith_by_id(hadith_id)
            if hadith:
                hadiths.append(hadith)
    
    return hadiths
```

---

## 🛡️ BONNES PRATIQUES

### Rate Limiting

```python
# Toujours respecter un délai entre requêtes
RATE_LIMITS = {
    "dorar": 2.0,      # 2 secondes minimum
    "shamela": 3.0,    # 3 secondes minimum
    "sunnah": 2.0      # 2 secondes minimum
}

await asyncio.sleep(RATE_LIMITS["dorar"])
```

### Gestion des erreurs

```python
async def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
    """
    Fetch avec retry automatique
    """
    for attempt in range(max_retries):
        try:
            result = await self._fetch_with_mcp(url)
            if result:
                return result
        except Exception as e:
            print(f"❌ Tentative {attempt + 1}/{max_retries} échouée: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5 * (attempt + 1))  # Backoff exponentiel
    
    return None
```

### Cache intelligent

```python
# Toujours vérifier le cache avant de faire une requête MCP
cache_key = f"{book_key}_{hadith_id}"
if cache_key in self.cache:
    return self.cache[cache_key]

# Faire la requête MCP
result = await self._fetch_with_mcp(url)

# Sauvegarder dans le cache
if result:
    self.cache[cache_key] = result
```

---

## 📈 MONITORING DES APPELS MCP

### Statistiques à suivre

```python
self.session_stats = {
    "mcp_calls": 0,           # Nombre d'appels MCP
    "mcp_success": 0,         # Appels réussis
    "mcp_errors": 0,          # Appels échoués
    "cache_hits": 0,          # Hits du cache
    "avg_response_time": 0.0  # Temps de réponse moyen
}
```

### Affichage des stats

```python
def print_mcp_stats(self):
    """Affiche les statistiques MCP"""
    print("\n📊 STATISTIQUES MCP")
    print(f"   Appels totaux: {self.session_stats['mcp_calls']}")
    print(f"   Succès: {self.session_stats['mcp_success']}")
    print(f"   Erreurs: {self.session_stats['mcp_errors']}")
    print(f"   Cache hits: {self.session_stats['cache_hits']}")
    
    hit_rate = self.session_stats['cache_hits'] / max(self.session_stats['mcp_calls'], 1) * 100
    print(f"   Taux de cache: {hit_rate:.1f}%")
```

---

## 🚦 STATUT ACTUEL

### Mode actuel: SIMULATION
- ✅ Connecteur MCP créé
- ✅ Structure de données conforme
- ✅ Filtres Salaf appliqués
- ⏳ Scraping réel en attente d'activation

### Pour activer le mode réel:
1. Tester les extensions MCP individuellement
2. Implémenter le parsing HTML de Dorar
3. Valider sur un petit échantillon (10-20 hadiths)
4. Lancer en production avec `--mcp`

---

## 📝 CHECKLIST D'ACTIVATION

- [ ] Tester Tavily Search avec une requête simple
- [ ] Tester Browser MCP avec navigation Dorar
- [ ] Implémenter `_parse_dorar_html()`
- [ ] Tester sur 10 hadiths réels
- [ ] Valider la conformité des données
- [ ] Ajuster le rate limiting si nécessaire
- [ ] Lancer production avec `--mcp`

---

## 🔗 RESSOURCES

### Documentation MCP
- Tavily: https://docs.tavily.com/
- Browser MCP: https://github.com/BrowserMCP/mcp
- Playwright MCP: https://github.com/microsoft/playwright-mcp

### Sources de hadiths
- Dorar.net: https://dorar.net
- Shamela.ws: https://shamela.ws
- Sunnah.com: https://sunnah.com

---

**🕋 Bismillah - Que Allah facilite l'activation de ces outils pour préserver la Sunnah authentique.**

---

*Dernière mise à jour: 2026-04-18 03:14 AM*
*Statut: Guide complet - Prêt pour activation*