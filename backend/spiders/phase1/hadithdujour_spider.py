"""
Spider — hadithdujour.com
Hadith-du-jour posts one authenticated hadith per day with Arabic + French translation.
Strategy: crawl homepage → extract current hadith → follow pagination/archive links.
"""

import re
from typing import Optional, Set
from urllib.parse import urljoin, urlparse

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.hadithdujour")

START_URL = "https://www.hadithdujour.com"
MAX_PAGES = 80  # safety cap


class HadithDuJourSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "hadithdujour")

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

            # Extract hadiths from this page
            extracted = self._extract_hadiths(soup, url)
            for entry in extracted:
                self.process(entry)

            # Discover next page / archive links
            for link in self._find_pagination(soup, url):
                if link not in visited:
                    queue.append(link)

        log.info(f"[hadithdujour] Done: {self.stats['extracted']} hadiths from {self.stats['pages_crawled']} pages")

    def _extract_hadiths(self, soup, page_url: str):
        """Extract hadith entries from a page."""
        entries = []

        # Try post-level containers (WordPress blog structure)
        containers = (
            soup.select("article.post")
            or soup.select(".post")
            or soup.select(".entry")
            or soup.select(".hadith-container")
            or [soup]
        )

        for container in containers:
            entry = self._parse_container(container, page_url)
            if entry:
                entries.append(entry)

        return entries

    def _parse_container(self, container, page_url: str) -> Optional[HadithEntry]:
        text_all = container.get_text(" ", strip=True)

        # Arabic text
        matn_ar = self.extract_arabic(container)

        # French translation — look for text after "Traduction" or "Il a dit"
        matn_fr = self._extract_fr(container)

        # Skip if nothing useful
        if not matn_ar and not matn_fr:
            return None
        if matn_fr and len(matn_fr.strip()) < 15:
            return None

        # Grade detection
        grade = normalise_grade(text_all)

        # Collection detection
        collection = normalise_collection(text_all)

        # Hadith number
        num_match = re.search(r'\b(?:n[°o]?\.?\s*)(\d+)\b', text_all, re.I)
        numero = num_match.group(1) if num_match else None

        # Translator (look for "Traduit par" / "Traduction :")
        translator = self._extract_translator(text_all)

        # Canonical page URL
        source_url = self._canonical_url(container, page_url)

        return HadithEntry(
            matn_ar=matn_ar,
            matn_fr=matn_fr,
            collection=collection,
            numero_hadith=numero,
            livre=None,
            chapitre=None,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=source_url,
            translator=translator,
        )

    def _extract_fr(self, container) -> Optional[str]:
        """Extract French translation, preferring elements after Arabic block."""
        # Common class names
        for sel in [".traduction", ".trad", ".translation", ".hadith-fr",
                    ".francais", ".french", ".contenu-fr"]:
            el = container.select_one(sel)
            if el:
                t = el.get_text(" ", strip=True)
                if t and len(t) > 15:
                    return t

        # Walk paragraphs: first <p> without Arabic = French translation
        paras = container.find_all("p")
        arabic_seen = False
        for p in paras:
            txt = p.get_text(" ", strip=True)
            if _AR_RE.search(txt):
                arabic_seen = True
                continue
            if arabic_seen and len(txt) > 20:
                return txt

        # Fallback: any non-empty <p>
        for p in paras:
            txt = p.get_text(" ", strip=True)
            if not _AR_RE.search(txt) and len(txt) > 30:
                return txt

        return None

    def _extract_translator(self, text: str) -> Optional[str]:
        m = re.search(
            r'(?:traduit\s+par|traduction\s*:?|par\s+le\s+sheikh)\s+([A-ZÀ-Ö][^\n,.]{3,40})',
            text, re.I
        )
        return m.group(1).strip() if m else None

    def _canonical_url(self, container, page_url: str) -> str:
        # Try to find permalink
        link = container.find("a", href=re.compile(r'/\d{4}/\d{2}|/hadith-'))
        if link and link.get("href"):
            return self.abs_url(page_url, link["href"])
        return page_url

    def _find_pagination(self, soup, current_url: str):
        """Return next-page and archive links to follow."""
        links = []
        base = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}"

        # Pagination: next page button
        for sel in [".nav-previous a", ".older-posts", "a.next", ".pagination a"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                links.append(self.abs_url(current_url, el["href"]))

        # Archive month links (limit: first 12)
        archive_links = soup.select("ul.archives a, .widget_archive a")[:12]
        for a in archive_links:
            href = a.get("href", "")
            if base in href or href.startswith("/"):
                links.append(self.abs_url(current_url, href))

        return links
