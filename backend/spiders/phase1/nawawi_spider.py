"""
Spider — 40-hadith-nawawi.com
Dedicated site for the 40 Hadiths of Imam an-Nawawi (+ 2 by Ibn Rajab = 42).
Strategy: parse hadith-list/index page → crawl each individual hadith page.
"""

import re
from typing import List, Optional, Set

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.nawawi")

START_URL = "https://www.40-hadith-nawawi.com"
COLLECTION = "Arba'in an-Nawawi"


class NawawiSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "nawawi")

    async def crawl(self):
        html = await self.fetch(START_URL)
        if not html:
            log.error("[nawawi] Cannot reach start URL")
            return

        self.stats["pages_crawled"] += 1
        soup = self.soup(html)

        # Try to extract all hadiths from a single long page first
        inline = self._extract_inline(soup, START_URL)
        if inline:
            for e in inline:
                self.process(e)

        # Also collect links to individual hadith pages
        hadith_urls = self._collect_hadith_urls(soup, START_URL)
        visited: Set[str] = {START_URL}

        for url in hadith_urls:
            if url in visited:
                continue
            visited.add(url)

            hhtml = await self.fetch(url)
            if not hhtml:
                continue
            self.stats["pages_crawled"] += 1
            hsoup = self.soup(hhtml)

            entry = self._parse_hadith_page(hsoup, url)
            if entry:
                self.process(entry)

    def _collect_hadith_urls(self, soup, base_url: str) -> List[str]:
        """Collect links that look like individual hadith pages."""
        urls = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_href = self.abs_url(base_url, href)
            # Match patterns like /hadith-1/, /hadith/1, /#hadith1, /1, etc.
            if re.search(
                r'(?:hadith[-_/]?\d+|/\d{1,2}(?:/|$)|hadith=\d+)',
                abs_href, re.I
            ):
                if abs_href not in urls:
                    urls.append(abs_href)
        return urls[:50]  # max 50 individual pages

    def _extract_inline(self, soup, page_url: str) -> List[HadithEntry]:
        """Try to extract multiple hadiths from a single page."""
        entries = []

        # Look for numbered sections (h2/h3 like "Hadith 1", "Hadith n°1")
        headers = soup.find_all(re.compile(r'^h[2-4]$'))
        for h in headers:
            title = h.get_text(strip=True)
            num_match = re.search(r'\b(\d{1,2})\b', title)
            if not num_match:
                continue
            numero = num_match.group(1)

            # Gather sibling content until next header
            section_text = title
            section_soup_parts = []
            sibling = h.find_next_sibling()
            while sibling and sibling.name not in ('h2', 'h3', 'h4'):
                section_text += " " + sibling.get_text(" ", strip=True)
                section_soup_parts.append(sibling)
                sibling = sibling.find_next_sibling()

            matn_ar = None
            matn_fr = None

            for part in section_soup_parts:
                txt = part.get_text(" ", strip=True)
                if _AR_RE.search(txt) and not matn_ar:
                    matn_ar = txt
                elif not _AR_RE.search(txt) and len(txt) > 20 and not matn_fr:
                    matn_fr = txt

            if not matn_ar and not matn_fr:
                continue

            grade = normalise_grade(section_text)

            entries.append(HadithEntry(
                matn_ar=matn_ar,
                matn_fr=matn_fr,
                collection=COLLECTION,
                numero_hadith=numero,
                livre=None,
                chapitre=None,
                grade_final=grade,
                categorie=grade_to_category(grade),
                source_url=page_url,
                translator=None,
            ))

        return entries

    def _parse_hadith_page(self, soup, url: str) -> Optional[HadithEntry]:
        text_all = soup.get_text(" ", strip=True)

        matn_ar = self.extract_arabic(soup)
        matn_fr = self.extract_french(soup)

        if not matn_ar and not matn_fr:
            return None

        # Number from URL or page title
        num_match = re.search(r'(?:hadith[-_/]?)(\d+)', url, re.I)
        if not num_match:
            title_el = soup.find("h1") or soup.find("title")
            if title_el:
                num_match = re.search(r'\b(\d{1,2})\b', title_el.get_text())
        numero = num_match.group(1) if num_match else None

        grade = normalise_grade(text_all)

        return HadithEntry(
            matn_ar=matn_ar,
            matn_fr=matn_fr,
            collection=COLLECTION,
            numero_hadith=numero,
            livre=None,
            chapitre=None,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=url,
            translator=None,
        )
