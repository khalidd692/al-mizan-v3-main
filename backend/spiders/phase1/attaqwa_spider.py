"""
Spider — at-taqwa.fr/lexplication-de-omdatul-al-ahkam/
Explanation of Omdatu al-Ahkam — may be paginated or single long page.
Strategy: fetch start URL, detect pagination, extract all hadiths.
"""

import re
from typing import List, Optional, Set

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.attaqwa")

START_URL = "https://www.at-taqwa.fr/lexplication-de-omdatul-al-ahkam/"
COLLECTION = "Omdatu al-Ahkam"
TRANSLATOR = "at-taqwa.fr"
MAX_PAGES = 30


class AtTaqwaSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "attaqwa")

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

            entries = self._extract_page(soup, url)
            for e in entries:
                self.process(e)

            # Pagination
            for nxt in self._next_pages(soup, url):
                if nxt not in visited:
                    queue.append(nxt)

            # Sub-pages (individual hadith explanations)
            for sub in self._sub_links(soup, url):
                if sub not in visited:
                    queue.append(sub)

    def _next_pages(self, soup, current_url: str) -> List[str]:
        nexts = []
        for sel in ["a.next", "a[rel='next']", ".nav-next a", ".pagination a.next"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                nexts.append(self.abs_url(current_url, el["href"]))
                break
        return nexts

    def _sub_links(self, soup, base_url: str) -> List[str]:
        """Collect sub-page links that look like individual hadith explanations."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_href = self.abs_url(base_url, href)
            if re.search(
                r'omdatu?l?[-_/]?al[-_/]?ahkam|hadith[-_/]\d+',
                abs_href, re.I
            ) and abs_href != base_url and abs_href not in links:
                links.append(abs_href)
        return links[:60]

    def _extract_page(self, soup, page_url: str) -> List[HadithEntry]:
        content = (
            soup.select_one(".entry-content")
            or soup.select_one(".post-content")
            or soup.select_one("article")
            or soup.select_one("main")
            or soup.body
        )
        if not content:
            return []

        text_all = content.get_text(" ", strip=True)
        entries = []

        # Strategy A: section-by-section via headers
        headers = content.find_all(re.compile(r'^h[2-5]$'))
        if headers:
            for h in headers:
                h_text = h.get_text(strip=True)
                num_match = re.search(r'\b(\d{1,3})\b', h_text)
                numero = num_match.group(1) if num_match else None
                chapitre = h_text[:200]

                block = []
                sib = h.find_next_sibling()
                while sib and sib.name not in ('h2', 'h3', 'h4'):
                    block.append(sib)
                    sib = sib.find_next_sibling()

                block_text = " ".join(
                    p.get_text(" ", strip=True) for p in block if hasattr(p, 'get_text')
                )
                if len(block_text) < 20:
                    continue

                matn_ar, matn_fr = self._split_ar_fr(block)
                if not matn_ar and not matn_fr:
                    continue

                grade = normalise_grade(block_text + " " + h_text)
                entries.append(HadithEntry(
                    matn_ar=matn_ar, matn_fr=matn_fr,
                    collection=COLLECTION,
                    numero_hadith=numero,
                    livre=None, chapitre=chapitre,
                    grade_final=grade,
                    categorie=grade_to_category(grade),
                    source_url=page_url,
                    translator=TRANSLATOR,
                ))

        # Strategy B: paragraph pairs
        if not entries:
            entries = self._para_pairs(content, page_url)

        # Strategy C: whole page single entry
        if not entries:
            matn_ar = self.extract_arabic(content)
            matn_fr = self.extract_french(content)
            if matn_ar or matn_fr:
                grade = normalise_grade(text_all)
                entries.append(HadithEntry(
                    matn_ar=matn_ar, matn_fr=matn_fr,
                    collection=COLLECTION,
                    numero_hadith=None,
                    livre=None, chapitre=None,
                    grade_final=grade,
                    categorie=grade_to_category(grade),
                    source_url=page_url,
                    translator=TRANSLATOR,
                ))

        return entries

    def _split_ar_fr(self, block) -> tuple:
        matn_ar, matn_fr = None, None
        for part in block:
            if not hasattr(part, 'get_text'):
                continue
            txt = part.get_text(" ", strip=True)
            if _AR_RE.search(txt) and not matn_ar:
                matn_ar = txt
            elif not _AR_RE.search(txt) and len(txt) > 15 and not matn_fr:
                matn_fr = txt
        return matn_ar, matn_fr

    def _para_pairs(self, content, page_url: str) -> List[HadithEntry]:
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
                        livre=None, chapitre=None,
                        grade_final=grade,
                        categorie=grade_to_category(grade),
                        source_url=page_url,
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
                livre=None, chapitre=None,
                grade_final=grade,
                categorie=grade_to_category(grade),
                source_url=page_url,
                translator=TRANSLATOR,
            ))

        return entries
