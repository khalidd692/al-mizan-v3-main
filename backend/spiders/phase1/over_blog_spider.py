"""
Spider — bibliotheque-islamique-coran-sunna.over-blog.com
Over-Blog platform blog on Islamic content.
Strategy: parse blog index → individual article pages.
"""

import re
from typing import List, Optional, Set

from backend.spiders.base_spider import (
    BaseSpider, HadithEntry, normalise_collection, normalise_grade,
    grade_to_category, _AR_RE
)
from backend.utils.logging import get_logger

log = get_logger("mizan.spider.overblog")

START_URL = "https://bibliotheque-islamique-coran-sunna.over-blog.com"
MAX_PAGES = 50


class OverBlogSpider(BaseSpider):

    def __init__(self):
        super().__init__(START_URL, "over_blog_bibl_islamique")

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

            # Collect article links
            articles = self._collect_article_links(soup, url)
            for link in articles:
                if link not in visited:
                    queue.append(link)

            # Next page of blog index
            nxt = self._next_page(soup, url)
            if nxt and nxt not in visited:
                queue.append(nxt)

            # If this looks like an article page, extract hadiths
            if self._is_article_page(soup):
                entries = self._extract_from_article(soup, url)
                for e in entries:
                    self.process(e)

    def _is_article_page(self, soup) -> bool:
        """Heuristic: article page has a single main <article> or .article-content."""
        return bool(
            soup.select_one("article.article")
            or soup.select_one(".article-content")
            or soup.select_one(".post-content")
        )

    def _collect_article_links(self, soup, base_url: str) -> List[str]:
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            abs_href = self.abs_url(base_url, href)
            # over-blog articles typically have date paths like /2023/01/article-title.html
            if re.search(r'/\d{4}/\d{2}/.+\.html', abs_href):
                if abs_href not in links:
                    links.append(abs_href)
        return links[:100]

    def _next_page(self, soup, current_url: str) -> Optional[str]:
        for sel in ["a.next-page", "a[rel='next']", ".pagination a.next"]:
            el = soup.select_one(sel)
            if el and el.get("href"):
                return self.abs_url(current_url, el["href"])
        # over-blog pagination: ?page=N
        m = re.search(r'[?&]page=(\d+)', current_url)
        if m:
            nxt = int(m.group(1)) + 1
            return re.sub(r'([?&]page=)\d+', rf'\g<1>{nxt}', current_url)
        return None

    def _extract_from_article(self, soup, page_url: str) -> List[HadithEntry]:
        entries = []

        content = (
            soup.select_one(".article-content")
            or soup.select_one(".post-content")
            or soup.select_one("article")
            or soup
        )

        text_all = content.get_text(" ", strip=True)

        # Try to find multiple hadiths in one article
        # Pattern: Arabic paragraph followed by French paragraph, repeated
        paras = content.find_all(["p", "div"])
        ar_buf, fr_buf = None, None
        count = 0

        for el in paras:
            txt = el.get_text(" ", strip=True)
            if len(txt) < 10:
                continue

            if _AR_RE.search(txt) and len(txt) > 15:
                # Flush previous pair
                if ar_buf and fr_buf:
                    e = self._make_entry(ar_buf, fr_buf, text_all, page_url, count)
                    if e:
                        entries.append(e)
                        count += 1
                    ar_buf, fr_buf = None, None
                ar_buf = txt

            elif ar_buf and not _AR_RE.search(txt) and len(txt) > 20:
                fr_buf = txt
                # If we have a complete pair, flush immediately
                e = self._make_entry(ar_buf, fr_buf, text_all, page_url, count)
                if e:
                    entries.append(e)
                    count += 1
                ar_buf, fr_buf = None, None

        # Tail pair
        if ar_buf and fr_buf:
            e = self._make_entry(ar_buf, fr_buf, text_all, page_url, count)
            if e:
                entries.append(e)

        # If nothing found with pairs, try single extraction
        if not entries:
            matn_ar = self.extract_arabic(content)
            matn_fr = self.extract_french(content)
            if matn_ar or matn_fr:
                grade = normalise_grade(text_all)
                coll = normalise_collection(text_all)
                entries.append(HadithEntry(
                    matn_ar=matn_ar,
                    matn_fr=matn_fr,
                    collection=coll,
                    numero_hadith=None,
                    livre=None,
                    chapitre=None,
                    grade_final=grade,
                    categorie=grade_to_category(grade),
                    source_url=page_url,
                    translator=None,
                ))

        return entries

    def _make_entry(self, matn_ar, matn_fr, context_text, page_url, idx) -> Optional[HadithEntry]:
        if not matn_ar and not matn_fr:
            return None
        grade = normalise_grade(context_text)
        coll = normalise_collection(context_text)
        return HadithEntry(
            matn_ar=matn_ar,
            matn_fr=matn_fr,
            collection=coll,
            numero_hadith=str(idx + 1),
            livre=None,
            chapitre=None,
            grade_final=grade,
            categorie=grade_to_category(grade),
            source_url=page_url,
            translator=None,
        )
