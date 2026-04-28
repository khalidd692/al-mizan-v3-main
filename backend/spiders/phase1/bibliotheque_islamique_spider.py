"""
Spider — bibliotheque-islamique.fr/hadith/
French Islamic library — hadith section.
Strategy: crawl paginated list → individual hadith pages.
"""

import re
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.bibl_islamique")

START_URL = "https://bibliotheque-islamique.fr/hadith/"
MAX_PAGES = 60


class BibliothequeIslamisqueSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "bibliotheque_islamique")

    async def crawl(self):
        visited: Set[str] = set()
        queue = [START_URL]

        while queue and self.stats["pages_crawled"] < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            html = await self.fetch(url)
            if not html:
                continue
            self.stats["pages_crawled"] += 1
            soup = self.soup(html)

            # Is this a list page or a single hadith page?
            hadith_links = self._collect_hadith_links(soup, url)

            if hadith_links:
                # List page: enqueue individual hadiths
                for link in hadith_links:
                    if link not in visited:
                        queue.append(link)
                # Also look for "next page" pagination
                for nxt in self._next_pages(soup, url):
                    if nxt not in visited:
                        queue.append(nxt)
            else:
                # Single hadith page: extract directly
                entry = self._parse_hadith_page(soup, url)
                if entry:
                    self.process(entry)

    def _collect_hadith_links(self, soup, base_url: str) -> List[str]:
        """Find links to individual hadith sub-pages."""
        links = []
        base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"

        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_href = self.abs_url(base_url, href)
            # Must be on the same domain and under /hadith/
            if base in abs_href and '/hadith/' in abs_href and abs_href != base_url:
                # Avoid pagination links
                if not re.search(r'[?&](?:page|p)=\d+', abs_href):
                    if abs_href not in links:
                        links.append(abs_href)

        return links[:200]

    def _next_pages(self, soup, current_url: str) -> List[str]:
        pages = []
        for sel in ["a.next", ".nav-next a", ".pagination a[rel='next']", "a[rel='next']"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                pages.append(self.abs_url(current_url, el["href"]))
                break
        return pages

    def _parse_hadith_page(self, soup, url: str) -> Optional[HadithEntry]:
        text_all = soup.get_text(" ", strip=True)

        # Content zone
        content = (
            soup.select_one("article")
            or soup.select_one(".entry-content")
            or soup.select_one(".post-content")
            or soup.select_one("main")
            or soup
        )

        matn_ar = self.extract_arabic(content)
        matn_fr = self._best_french(content, text_all)

        if not matn_ar and not matn_fr:
            return None

        grade = normalise_grade(text_all)
        collection = normalise_collection(text_all)

        # Hadith number
        num_match = re.search(r'\bhadith\s+n[°o]?\.?\s*(\d+)\b', text_all, re.I)
        if not num_match:
            num_match = re.search(r'\bn[°o]?\.?\s*(\d+)\b', text_all)
        numero = num_match.group(1) if num_match else None

        # Title for livre/chapitre
        title = (soup.find("h1") or soup.find("h2"))
        chapitre = title.get_text(strip=True)[:200] if title else None

        # Translator
        trans_m = re.search(
            r'(?:traduit(?:\s+par)?|traduction\s*:?|par\s+le?\s+sheikh)\s+([A-ZÀ-Ö][^\n,.<]{3,50})',
            text_all, re.I
        )
        translator = trans_m.group(1).strip() if trans_m else None

        return HadithEntry(
            matn_ar=matn_ar,
            matn_fr=matn_fr,
            collection=collection,
            numero_hadith=numero,
            livre=None,
            chapitre=chapitre,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=url,
            translator=translator,
        )

    def _best_french(self, content, full_text: str) -> Optional[str]:
        """Multi-strategy French extraction."""
        # 1. Specific class
        for sel in [".traduction", ".trad", ".hadith-fr", ".translation",
                    ".texte-francais", ".francais"]:
            el = content.select_one(sel)
            if el:
                t = el.get_text(" ", strip=True)
                if t and len(t) > 20:
                    return t

        # 2. Blockquote without Arabic
        for bq in content.find_all("blockquote"):
            t = bq.get_text(" ", strip=True)
            if not _AR_RE.search(t) and len(t) > 20:
                return t

        # 3. First substantial <p> after Arabic block
        ar_found = False
        for p in content.find_all("p"):
            t = p.get_text(" ", strip=True)
            if _AR_RE.search(t):
                ar_found = True
            elif ar_found and len(t) > 20:
                return t

        # 4. First substantial <p> overall
        for p in content.find_all("p"):
            t = p.get_text(" ", strip=True)
            if not _AR_RE.search(t) and len(t) > 30:
                return t

        return None
