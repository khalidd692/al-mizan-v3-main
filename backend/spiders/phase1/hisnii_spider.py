"""
Spider — hisnii.com/40-hadith-qudsi/
40 Hadiths Qudsi translated into French.
Strategy: single URL page — parse all hadith blocks.
"""

import re
from typing import List, Optional

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.hisnii")

START_URL = "https://www.hisnii.com/40-hadith-qudsi/"
COLLECTION = "Hadiths Qudsi"
TRANSLATOR = "hisnii.com"


class HisniiSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "hisnii")

    async def crawl(self):
        html = await self.fetch(START_URL)
        if not html:
            log.error("[hisnii] Cannot reach start URL")
            return

        self.stats["pages_crawled"] += 1
        soup = self.soup(html)

        # Try paginated sub-pages first
        subpages = self._collect_subpages(soup, START_URL)
        all_pages = [(START_URL, soup)] + []

        for sub_url in subpages:
            sub_html = await self.fetch(sub_url)
            if sub_html:
                self.stats["pages_crawled"] += 1
                all_pages.append((sub_url, self.soup(sub_html)))

        for page_url, page_soup in all_pages:
            entries = self._extract_hadiths(page_soup, page_url)
            for e in entries:
                self.process(e)

    def _collect_subpages(self, soup, base_url: str) -> List[str]:
        urls = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if re.search(r'hadith.qudsi|qudsi-\d+|/\d+(?:/|$)', href, re.I):
                abs_href = self.abs_url(base_url, href)
                if abs_href not in urls and abs_href != base_url:
                    urls.append(abs_href)
        return urls[:45]

    def _extract_hadiths(self, soup, page_url: str) -> List[HadithEntry]:
        entries = []

        # Strategy A: look for numbered hadith blocks
        # Many sites use <div class="hadith"> or <article> per hadith
        containers = (
            soup.select(".hadith")
            or soup.select(".hadith-qudsi")
            or soup.select("article")
            or soup.select(".entry-content .hadith")
        )

        if containers:
            for i, c in enumerate(containers, 1):
                e = self._parse_block(c, page_url, str(i))
                if e:
                    entries.append(e)
        else:
            # Strategy B: parse the whole page content as one block
            entries = self._parse_single_page(soup, page_url)

        return entries

    def _parse_block(self, container, page_url: str, default_num: str) -> Optional[HadithEntry]:
        text = container.get_text(" ", strip=True)

        matn_ar = self.extract_arabic(container)
        matn_fr = self.extract_french(container)

        if not matn_ar and not matn_fr:
            return None

        num_match = re.search(r'\b(\d{1,2})\b', text)
        numero = num_match.group(1) if num_match else default_num
        grade = normalise_grade(text)

        # Try to find source collection mentioned
        src_match = re.search(r'(?:rapporté par|selon|d\'après)\s+([^,.\n]{4,50})', text, re.I)
        collection = src_match.group(1).strip() if src_match else COLLECTION

        return HadithEntry(
            matn_ar=matn_ar,
            matn_fr=matn_fr,
            collection=collection,
            numero_hadith=numero,
            livre=None,
            chapitre=None,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=page_url,
            translator=TRANSLATOR,
        )

    def _parse_single_page(self, soup, page_url: str) -> List[HadithEntry]:
        """Parse a single long page with multiple hadiths separated by headers."""
        entries = []
        content = soup.find("div", class_=re.compile(r'content|entry|post'))
        if not content:
            content = soup.body

        if not content:
            return entries

        # Split by h2/h3 headers (each = one hadith)
        current_num = None
        current_parts = []

        for el in content.children:
            if not hasattr(el, 'name'):
                continue
            if el.name in ('h2', 'h3', 'h4'):
                # Flush previous hadith
                if current_parts:
                    e = self._flush(current_parts, current_num, page_url)
                    if e:
                        entries.append(e)
                    current_parts = []
                header_text = el.get_text(strip=True)
                m = re.search(r'\b(\d{1,2})\b', header_text)
                current_num = m.group(1) if m else str(len(entries) + 1)
            else:
                current_parts.append(el)

        # Last block
        if current_parts:
            e = self._flush(current_parts, current_num, page_url)
            if e:
                entries.append(e)

        # Fallback: if nothing found, try arabic/french pairs from all <p>
        if not entries:
            paras = content.find_all("p")
            ar_buf, fr_buf = None, None
            count = 0
            for p in paras:
                txt = p.get_text(" ", strip=True)
                if _AR_RE.search(txt):
                    if ar_buf and fr_buf:
                        grade = normalise_grade(ar_buf + " " + fr_buf)
                        entries.append(HadithEntry(
                            matn_ar=ar_buf, matn_fr=fr_buf,
                            collection=COLLECTION,
                            numero_hadith=str(count),
                            livre=None, chapitre=None,
                            grade_final=grade,
                            categorie=grade_to_category(grade),
                            source_url=page_url,
                            translator=TRANSLATOR,
                        ))
                        ar_buf, fr_buf = None, None
                    ar_buf = txt
                    count += 1
                elif len(txt) > 20:
                    fr_buf = txt

            if ar_buf and fr_buf:
                grade = normalise_grade(ar_buf + " " + fr_buf)
                entries.append(HadithEntry(
                    matn_ar=ar_buf, matn_fr=fr_buf,
                    collection=COLLECTION,
                    numero_hadith=str(count),
                    livre=None, chapitre=None,
                    grade_final=grade,
                    categorie=grade_to_category(grade),
                    source_url=page_url,
                    translator=TRANSLATOR,
                ))

        return entries

    def _flush(self, parts, numero, page_url: str) -> Optional[HadithEntry]:
        combined = " ".join(p.get_text(" ", strip=True) for p in parts if hasattr(p, 'get_text'))
        matn_ar, matn_fr = None, None
        for p in parts:
            if not hasattr(p, 'get_text'):
                continue
            txt = p.get_text(" ", strip=True)
            if _AR_RE.search(txt) and not matn_ar:
                matn_ar = txt
            elif not _AR_RE.search(txt) and len(txt) > 15 and not matn_fr:
                matn_fr = txt
        if not matn_ar and not matn_fr:
            return None
        grade = normalise_grade(combined)
        return HadithEntry(
            matn_ar=matn_ar, matn_fr=matn_fr,
            collection=COLLECTION,
            numero_hadith=numero,
            livre=None, chapitre=None,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=page_url,
            translator=TRANSLATOR,
        )
