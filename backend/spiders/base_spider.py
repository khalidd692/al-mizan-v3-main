"""
Al-Mīzān v5.0 — Base Spider
Provides robots.txt, rate limiting, checkpoints (every 500 entries),
UPSERT-only DB writes, and manhaj_classifier integration.
"""

import asyncio
import hashlib
import json
import pathlib
import random
import re
import sqlite3
import sys
import time
import urllib.robotparser
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

# Ensure backend package is importable when run directly
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.manhaj_classifier import classify, log_rejection
from backend.utils.logging import get_logger

log = get_logger("mizan.spider")

DB_PATH = _REPO_ROOT / "backend" / "almizane.db"
OUTPUT_DIR = _REPO_ROOT / "output" / "spider_data"
CHECKPOINT_INTERVAL = 500

# Arabic unicode range
_AR_RE = re.compile(r'[؀-ۿ]{4,}')

# Grade normalisation patterns
_GRADE_PATTERNS = [
    (re.compile(r'\b(sahih|ṣaḥīḥ|صحيح|authentique)\b', re.I), "Sahih"),
    (re.compile(r'\b(hasan|حسن|bon)\b', re.I), "Hasan"),
    (re.compile(r'\b(da.?if|ضعيف|faible)\b', re.I), "Da'if"),
    (re.compile(r'\b(mawdu.?|موضوع|fabriqu[eé])\b', re.I), "Mawdu'"),
]

# Collection normalisation
_COLL_PATTERNS = [
    (re.compile(r'bukh[aā]r[iī]', re.I), "Sahih al-Bukhari"),
    (re.compile(r'muslim', re.I), "Sahih Muslim"),
    (re.compile(r'ab[oū][\s-]d[aā]w[oū]d', re.I), "Sunan Abi Dawud"),
    (re.compile(r'tirmidh[iī]', re.I), "Sunan at-Tirmidhi"),
    (re.compile(r'nasa.[iī]', re.I), "Sunan an-Nasa'i"),
    (re.compile(r'ibn[\s-]m[aā]j[ah]', re.I), "Sunan Ibn Majah"),
    (re.compile(r'ahmad', re.I), "Musnad Ahmad"),
    (re.compile(r'nawaw[iī]|arba.?in', re.I), "Arba'in an-Nawawi"),
    (re.compile(r'riy[aā][dḍ].+s[aā]lih', re.I), "Riyadh as-Salihin"),
    (re.compile(r'omdatu?\s+al.ahk[aā]m|umdatu?\s+al.ahk[aā]m', re.I), "Omdatu al-Ahkam"),
    (re.compile(r'hisn.+muslim|forteres', re.I), "Hisn al-Muslim"),
    (re.compile(r'qudsi', re.I), "Hadiths Qudsi"),
]


def normalise_grade(text: str) -> Optional[str]:
    for pat, norm in _GRADE_PATTERNS:
        if pat.search(text):
            return norm
    return None


def normalise_collection(text: str) -> Optional[str]:
    for pat, norm in _COLL_PATTERNS:
        if pat.search(text):
            return norm
    return None


def grade_to_category(grade: Optional[str]) -> str:
    if not grade:
        return "UNKNOWN"
    g = grade.lower()
    if "sahih" in g or "hasan" in g:
        return "MAQBUL"
    if "da'if" in g or "daif" in g:
        return "DAIF"
    if "mawdu" in g:
        return "MAWDUU"
    return "UNKNOWN"


@dataclass
class HadithEntry:
    matn_ar: Optional[str]
    matn_fr: Optional[str]
    collection: Optional[str]
    numero_hadith: Optional[str]
    livre: Optional[str]
    chapitre: Optional[str]
    grade_final: Optional[str]
    categorie: str
    source_url: str
    translator: Optional[str]
    extraction_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    sha256: str = ""

    def compute_sha256(self) -> str:
        text = ((self.matn_ar or "").strip() + "|" + (self.matn_fr or "").strip())
        self.sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return self.sha256


class BaseSpider(ABC):
    """
    Base spider with:
    - robots.txt enforcement
    - Random 2-5s delay between requests
    - JSON checkpoint every 500 entries
    - UPSERT-only writes to almizane.db
    - manhaj_classifier pass-through
    - Full attribution preservation
    """

    USER_AGENT = "Al-Mizan Research Bot/5.0 (+https://al-mizan.info/bot; academic)"
    MIN_DELAY = 2.0
    MAX_DELAY = 5.0

    def __init__(self, start_url: str, spider_name: str):
        self.start_url = start_url
        self.name = spider_name
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_req = 0.0
        self._robots = urllib.robotparser.RobotFileParser()
        self._robots_loaded = False

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.data_file = OUTPUT_DIR / f"{spider_name}_data.json"

        self.stats: Dict[str, Any] = {
            "spider": spider_name,
            "start_url": start_url,
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "pages_crawled": 0,
            "extracted": 0,
            "accepted": 0,
            "rejected": 0,
            "db_inserted": 0,
            "db_updated": 0,
            "errors": 0,
        }
        self._all_entries: List[dict] = []

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "fr,ar;q=0.9,en;q=0.7",
            }
        )
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    # ── Networking ────────────────────────────────────────────────────────────

    def _load_robots(self):
        parsed = urlparse(self.start_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        self._robots.set_url(robots_url)
        try:
            self._robots.read()
        except Exception:
            pass
        self._robots_loaded = True

    def _allowed(self, url: str) -> bool:
        if not self._robots_loaded:
            self._load_robots()
        allowed = self._robots.can_fetch(self.USER_AGENT, url)
        if not allowed:
            log.warning(f"[{self.name}] robots.txt disallows: {url}")
        return allowed

    async def _wait(self):
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        elapsed = time.monotonic() - self._last_req
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_req = time.monotonic()

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch URL respecting robots.txt and rate limiting."""
        if not self._allowed(url):
            return None
        await self._wait()
        try:
            async with self.session.get(
                url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True
            ) as resp:
                if resp.status == 200:
                    ct = resp.headers.get("content-type", "")
                    if "html" in ct or "text" in ct:
                        return await resp.text(errors="replace")
                elif resp.status in (301, 302):
                    pass
                elif resp.status == 404:
                    log.debug(f"[{self.name}] 404: {url}")
                else:
                    log.warning(f"[{self.name}] HTTP {resp.status}: {url}")
                    self.stats["errors"] += 1
                return None
        except asyncio.TimeoutError:
            log.warning(f"[{self.name}] Timeout: {url}")
            self.stats["errors"] += 1
            return None
        except aiohttp.ClientError as e:
            log.error(f"[{self.name}] ClientError {url}: {e}")
            self.stats["errors"] += 1
            return None

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_checkpoint(self):
        payload = {
            "stats": self.stats,
            "entries": self._all_entries,
            "saved_at": datetime.utcnow().isoformat(),
        }
        try:
            with open(self.data_file, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            log.info(f"[{self.name}] Checkpoint: {len(self._all_entries)} entrées → {self.data_file.name}")
        except Exception as exc:
            log.error(f"[{self.name}] Checkpoint error: {exc}")

    def _upsert(self, entry: HadithEntry):
        """UPSERT into almizane.db — never drops existing data."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()

            # Check if exists to track insert vs update
            cur.execute("SELECT id FROM hadiths WHERE sha256 = ?", (entry.sha256,))
            exists = cur.fetchone() is not None

            cur.execute(
                """
                INSERT INTO hadiths
                    (sha256, collection, numero_hadith, livre, chapitre,
                     matn_ar, matn_fr, isnad_brut, grade_final, categorie,
                     badge_alerte, source_url, source_api, inserted_at)
                VALUES (?, ?, ?, ?, ?,  ?, ?, ?, ?, ?,  ?, ?, ?, datetime('now'))
                ON CONFLICT(sha256) DO UPDATE SET
                    matn_fr    = COALESCE(excluded.matn_fr,    hadiths.matn_fr),
                    grade_final= COALESCE(excluded.grade_final, hadiths.grade_final),
                    source_url = COALESCE(excluded.source_url,  hadiths.source_url)
                """,
                (
                    entry.sha256,
                    entry.collection or "Inconnu",
                    entry.numero_hadith,
                    entry.livre,
                    entry.chapitre,
                    entry.matn_ar,
                    entry.matn_fr,
                    None,
                    entry.grade_final or "INCONNU",
                    entry.categorie,
                    1 if entry.categorie == "MAWDUU" else 0,
                    entry.source_url,
                    f"spider_{self.name}",
                ),
            )
            conn.commit()
            conn.close()
            if exists:
                self.stats["db_updated"] += 1
            else:
                self.stats["db_inserted"] += 1
        except Exception as exc:
            log.error(f"[{self.name}] DB UPSERT error: {exc}")
            self.stats["errors"] += 1

    # ── Processing pipeline ───────────────────────────────────────────────────

    def process(self, entry: HadithEntry):
        """Run classifier → DB UPSERT → checkpoint if needed."""
        entry.compute_sha256()

        result = classify(
            matn_ar=entry.matn_ar,
            matn_fr=entry.matn_fr,
            source_url=entry.source_url,
            collection=entry.collection,
            grade=entry.grade_final,
            translator=entry.translator,
        )

        self.stats["extracted"] += 1

        entry_dict = asdict(entry)
        entry_dict["manhaj_score"] = result.score
        entry_dict["manhaj_accepted"] = result.accepted
        entry_dict["manhaj_reason"] = result.reason
        entry_dict["manhaj_flags"] = result.flags
        entry_dict["manhaj_category"] = result.manhaj_category

        if result.accepted:
            self.stats["accepted"] += 1
            entry.categorie = result.manhaj_category
            self._upsert(entry)
        else:
            self.stats["rejected"] += 1
            log_rejection(entry_dict, result)

        self._all_entries.append(entry_dict)

        if len(self._all_entries) % CHECKPOINT_INTERVAL == 0:
            self._save_checkpoint()

    # ── Main interface ────────────────────────────────────────────────────────

    @abstractmethod
    async def crawl(self):
        """Override in each concrete spider."""
        ...

    async def run(self) -> Dict[str, Any]:
        async with self:
            await self.crawl()
        self._save_checkpoint()
        self.stats["finished_at"] = datetime.utcnow().isoformat()
        return self._report()

    def _report(self) -> Dict[str, Any]:
        total = self.stats["extracted"]
        acc = self.stats["accepted"]
        rej = self.stats["rejected"]
        ins = self.stats["db_inserted"]
        upd = self.stats["db_updated"]

        return {
            "spider": self.name,
            "url": self.start_url,
            "pages_crawled": self.stats["pages_crawled"],
            "extracted": total,
            "accepted": acc,
            "rejected": rej,
            "acceptance_rate": f"{(acc/total*100):.1f}%" if total else "N/A",
            "db_inserted": ins,
            "db_updated": upd,
            "errors": self.stats["errors"],
            "started_at": self.stats["started_at"],
            "finished_at": self.stats["finished_at"],
            "data_file": str(self.data_file),
        }

    # ── HTML helpers shared by all spiders ───────────────────────────────────

    @staticmethod
    def soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def extract_arabic(soup: BeautifulSoup) -> Optional[str]:
        """Best-effort extraction of Arabic text block."""
        # 1. Elements with explicit Arabic/RTL attributes
        for sel in [
            "[lang='ar']", "[dir='rtl']",
            ".arabic", ".ar", ".hadith-ar", ".matn-ar",
            ".hadith_arabe", ".texte-arabe", ".arabe",
            "blockquote",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(" ", strip=True)
                if _AR_RE.search(txt):
                    return txt
        # 2. Any element whose text contains ≥10 Arabic chars
        for el in soup.find_all(["p", "div", "span"]):
            txt = el.get_text(" ", strip=True)
            if len(_AR_RE.findall(txt)) >= 1 and len(txt) > 15:
                return txt
        return None

    @staticmethod
    def extract_french(soup: BeautifulSoup, skip_arabic: bool = True) -> Optional[str]:
        """Best-effort extraction of French translation block."""
        # Common class names used by French Islamic sites
        for sel in [
            ".traduction", ".trad", ".hadith-fr", ".matn-fr",
            ".hadith_francais", ".texte-francais", ".francais",
            ".translation", ".hadith-traduction",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(" ", strip=True)
                if txt and len(txt) > 20:
                    return txt
        # Fallback: first <p> without Arabic chars
        for el in soup.find_all("p"):
            txt = el.get_text(" ", strip=True)
            if len(txt) > 30 and not _AR_RE.search(txt):
                return txt
        return None

    @staticmethod
    def find_grade(text: str) -> Optional[str]:
        return normalise_grade(text)

    @staticmethod
    def find_collection(text: str) -> Optional[str]:
        return normalise_collection(text)

    @staticmethod
    def abs_url(base: str, href: str) -> str:
        return urljoin(base, href)
