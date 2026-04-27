"""
Spider — dammaj-fr.com/omdatu-al-ahkam-le-livre-de-la-salat-complet/
One long page: Omdatu al-Ahkam — Livre de la Salat (complet).
Strategy: parse single page, extract each hadith entry.
"""

import re
from typing import List, Optional

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.dammaj")

START_URL = "https://dammaj-fr.com/omdatu-al-ahkam-le-livre-de-la-salat-complet/"
COLLECTION = "Omdatu al-Ahkam"
TRANSLATOR = "dammaj-fr.com"


class DammajSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "dammaj")

    async def crawl(self):
        html = await self.fetch(START_URL)
        if not html:
            log.error("[dammaj] Cannot reach start URL")
            return

        self.stats["pages_crawled"] += 1
        soup = self.soup(html)

        entries = self._extract_all(soup)
        for e in entries:
            self.process(e)

        log.info(f"[dammaj] Extracted {len(entries)} hadiths from single page")

        # Also check for paginated continuation
        next_page = self._find_next(soup)
        if next_page:
            next_html = await self.fetch(next_page)
            if next_html:
                self.stats["pages_crawled"] += 1
                next_soup = self.soup(next_html)
                for e in self._extract_all(next_soup):
                    self.process(e)

    def _find_next(self, soup) -> Optional[str]:
        for sel in ["a.next", "a[rel='next']", ".nav-next a"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                return self.abs_url(START_URL, el["href"])
        return None

    def _extract_all(self, soup) -> List[HadithEntry]:
        entries = []

        content = (
            soup.select_one(".entry-content")
            or soup.select_one(".post-content")
            or soup.select_one("article")
            or soup.select_one("main")
            or soup.body
        )

        if not content:
            return entries

        # Strategy A: hadith blocks separated by headers
        entries = self._extract_by_headers(content)
        if entries:
            return entries

        # Strategy B: Arabic/French paragraph pairs
        entries = self._extract_by_para_pairs(content)
        if entries:
            return entries

        # Strategy C: whole page as one block
        text_all = content.get_text(" ", strip=True)
        matn_ar = self.extract_arabic(content)
        matn_fr = self.extract_french(content)
        if matn_ar or matn_fr:
            grade = normalise_grade(text_all)
            entries.append(HadithEntry(
                matn_ar=matn_ar, matn_fr=matn_fr,
                collection=COLLECTION,
                numero_hadith=None,
                livre="Salat", chapitre=None,
                grade_final=grade,
                categorie=grade_to_category(grade),
                source_url=START_URL,
                translator=TRANSLATOR,
            ))

        return entries

    def _extract_by_headers(self, content) -> List[HadithEntry]:
        entries = []
        headers = content.find_all(re.compile(r'^h[2-5]$'))

        for h in headers:
            header_text = h.get_text(strip=True)
            num_match = re.search(r'\b(\d{1,3})\b', header_text)
            numero = num_match.group(1) if num_match else None

            # Chapter / livre from header
            chapitre = header_text[:200]

            # Collect block until next same-level header
            block_parts = []
            sib = h.find_next_sibling()
            stop_tags = {h.name, 'h1', 'h2', 'h3'}
            while sib and sib.name not in stop_tags:
                block_parts.append(sib)
                sib = sib.find_next_sibling()

            block_text = " ".join(p.get_text(" ", strip=True)
                                  for p in block_parts if hasattr(p, 'get_text'))
            if len(block_text) < 20:
                continue

            matn_ar, matn_fr = None, None
            for part in block_parts:
                if not hasattr(part, 'get_text'):
                    continue
                txt = part.get_text(" ", strip=True)
                if _AR_RE.search(txt) and not matn_ar:
                    matn_ar = txt
                elif not _AR_RE.search(txt) and len(txt) > 15 and not matn_fr:
                    matn_fr = txt

            if not matn_ar and not matn_fr:
                continue

            grade = normalise_grade(block_text + " " + header_text)
            entries.append(HadithEntry(
                matn_ar=matn_ar, matn_fr=matn_fr,
                collection=COLLECTION,
                numero_hadith=numero,
                livre="Salat",
                chapitre=chapitre,
                grade_final=grade,
                categorie=grade_to_category(grade),
                source_url=START_URL,
                translator=TRANSLATOR,
            ))

        return entries

    def _extract_by_para_pairs(self, content) -> List[HadithEntry]:
        entries = []
        paras = content.find_all(["p", "div"])
        ar_buf, fr_buf, count = None, None, 0

        for el in paras:
            if not hasattr(el, 'get_text'):
                continue
            txt = el.get_text(" ", strip=True)
            if len(txt) < 10:
                continue

            if _AR_RE.search(txt) and len(txt) > 15:
                if ar_buf and fr_buf:
                    grade = normalise_grade(ar_buf + " " + fr_buf)
                    entries.append(HadithEntry(
                        matn_ar=ar_buf, matn_fr=fr_buf,
                        collection=COLLECTION,
                        numero_hadith=str(count + 1),
                        livre="Salat", chapitre=None,
                        grade_final=grade,
                        categorie=grade_to_category(grade),
                        source_url=START_URL,
                        translator=TRANSLATOR,
                    ))
                    count += 1
                    ar_buf, fr_buf = None, None
                ar_buf = txt

            elif ar_buf and not _AR_RE.search(txt) and len(txt) > 20:
                fr_buf = txt

        if ar_buf and fr_buf:
            grade = normalise_grade(ar_buf + " " + fr_buf)
            entries.append(HadithEntry(
                matn_ar=ar_buf, matn_fr=fr_buf,
                collection=COLLECTION,
                numero_hadith=str(count + 1),
                livre="Salat", chapitre=None,
                grade_final=grade,
                categorie=grade_to_category(grade),
                source_url=START_URL,
                translator=TRANSLATOR,
            ))

        return entries
