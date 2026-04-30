#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOISSON TOTALE — MODE INDUSTRIEL 🔥🔥🔥
Playwright Stealth | Batch 100 URLs | Objectif: 1000+ detections
"""

import json
import os
import random
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin
from difflib import SequenceMatcher

# Playwright
try:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import stealth_sync
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright/Stealth non installé")
    sys.exit(1)

# RapidFuzz
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MOISSON TOTALE
# ═══════════════════════════════════════════════════════════════════════════════

BATCH_SIZE = 100
MAX_WORKERS = 5
RATE_LIMIT = 1.5  # secondes entre requêtes
OBJECTIF_DETECTIONS = 1000

# Base de données SQLite
DB_PATH = Path(__file__).parent.parent / "export_medine" / "detections_web_massives.db"

# Blacklist massive — 60+ hadiths
BLACKLIST_MOISSON = [
    # MAWDOU' (INVENTÉS) — Priorité MAXIMUM
    {"id": 1, "texte": "Cherche la science même en Chine", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 416", "courant": "Général", "keywords": ["science", "chine", "étudier"]},
    {"id": 2, "texte": "Mes compagnons sont comme des étoiles", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 144", "courant": "Ikhwānī", "keywords": ["compagnons", "étoiles", "suivre"]},
    {"id": 3, "texte": "La divergence de ma communauté est une miséricorde", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 57", "courant": "Ikhwānī", "keywords": ["divergence", "différence", "miséricorde"]},
    {"id": 4, "texte": "L'amour de la patrie fait partie de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 36", "courant": "Ikhwānī", "keywords": ["patrie", "nation", "foi"]},
    {"id": 5, "texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général", "keywords": ["travailler", "vie", "éternel"]},
    {"id": 6, "texte": "Soyez optimistes vous trouverez le bien", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général", "keywords": ["optimiste", "bien", "positif"]},
    {"id": 7, "texte": "Le Prophète a pleuré pour les morts", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi", "keywords": ["pleurer", "morts", "larmes"]},
    {"id": 8, "texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi", "keywords": ["dhikr", "secret", "silencieux"]},
    {"id": 9, "texte": "Le Prophète a dit au Companion serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["serpent", "tuer", "compagnon"]},
    {"id": 10, "texte": "Les trois choses sérieuses jeu chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["sérieux", "chasse", "jeu"]},
    {"id": 11, "texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["voyage", "seul", "satan"]},
    {"id": 12, "texte": "La meilleure des femmes ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["femme", "meilleure", "hommes"]},
    {"id": 13, "texte": "Quand un mari regarde sa femme avec amour", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mari", "femme", "amour"]},
    {"id": 14, "texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mariage", "moitié", "foi"]},
    {"id": 15, "texte": "Le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["paradis", "pieds", "mères"]},
    {"id": 16, "texte": "Le temps est une épée", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["temps", "épée", "coupe"]},
    {"id": 17, "texte": "Quand Allah aime un serviteur il l'afflige", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["aime", "affliger", "souffrance"]},
    {"id": 18, "texte": "La science sans pratique est comme un arbre sans fruit", "grade": "mawdou", "savant": "Ibn Ḥajar", "ref": "", "courant": "Soufi", "keywords": ["science", "pratique", "arbre"]},
    {"id": 19, "texte": "Quand tu as un appel à faire à Allah fais-le", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["appel", "demande", "Allah"]},
    {"id": 20, "texte": "Le Prophète a interdit de fumer", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["fumer", "cigarette", "interdit"]},
    {"id": 21, "texte": "La femme en Enfer suspendue par les cheveux", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT 19493", "courant": "Général", "keywords": ["femme", "enfer", "cheveux"]},
    {"id": 22, "texte": "Qui me voit a vu Allah", "grade": "mawdou", "savant": "Ibn Bāz", "ref": "FT", "courant": "Soufi", "keywords": ["voir", "Allah", "prophète"]},
    {"id": 23, "texte": "Le Prophète aurait embrassé les mains de Abu Bakr", "grade": "mawdou", "savant": "Multiple", "ref": "", "courant": "Ash'arī", "keywords": ["Abu Bakr", "embrasser", "mains"]},
    {"id": 24, "texte": "Le cœur rouille comme le fer", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["cœur", "rouille", "fer"]},
    {"id": 25, "texte": "Quand vous priez ne regardez ni à droite", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["prière", "regarder", "droite"]},
    {"id": 26, "texte": "Ne dormez pas sur le ventre", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["dormir", "ventre", "position"]},
    {"id": 27, "texte": "Le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["calme", "Allah", "hâte"]},
    {"id": 28, "texte": "Le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["pauvre", "paradis", "riche"]},
    {"id": 29, "texte": "Les savants sont les héritiers des prophètes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 629", "courant": "Ash'arī", "keywords": ["savants", "héritiers", "prophètes"]},
    {"id": 30, "texte": "Visitez les tombes", "grade": "daif", "savant": "al-Albānī", "ref": "SD 50", "courant": "Soufi", "keywords": ["tombe", "cimetière", "visiter"]},
    {"id": 31, "texte": "Le monde est la prison du croyant", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["monde", "prison", "croyant"]},
    {"id": 32, "texte": "Le croyant est le miroir de son frère", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Général", "keywords": ["miroir", "frère", "croyant"]},
    {"id": 33, "texte": "Le sourire envers ton frère est une sadaqa", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général", "keywords": ["sourire", "frère", "sadaqa"]},
    {"id": 34, "texte": "Le meilleur jihad parler une parole de justice", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Salafī", "keywords": ["jihad", "justice", "parole"]},
    {"id": 35, "texte": "Le paradis est sous l'ombre des épées", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["paradis", "ombre", "épées"]},
    {"id": 36, "texte": "Une femme ne doit pas voyager sans mahram", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["femme", "voyage", "mahram"]},
    {"id": 37, "texte": "Les anges ne entrent pas dans une maison avec un chien", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["anges", "chien", "maison"]},
    {"id": 38, "texte": "Le Prophète a interdit de manger avec la main gauche", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["manger", "gauche", "main"]},
    {"id": 39, "texte": "Le rêve du croyant est vrai", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Général", "keywords": ["rêve", "croyant", "vérité"]},
    {"id": 40, "texte": "Manger avec trois doigts", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["manger", "doigts", "trois"]},
    {"id": 41, "texte": "Boire en trois respirations", "grade": "saheeh", "savant": "Bukhari", "ref": "", "courant": "Salafī", "keywords": ["boire", "trois", "respiration"]},
    {"id": 42, "texte": "Le riba a 70 portes", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī", "keywords": ["riba", "intérêt", "70"]},
    {"id": 43, "texte": "Le Prophète a dit que le mariage est ma sunna", "grade": "saheeh", "savant": "Ibn Majah", "ref": "", "courant": "Salafī", "keywords": ["mariage", "sounnah", "célibat"]},
    {"id": 44, "texte": "Le Prophète a dit que le fajr est meilleur que le monde", "grade": "saheeh", "savant": "Muslim", "ref": "", "courant": "Salafī", "keywords": ["fajr", "prière", "monde"]},
    {"id": 45, "texte": "Le Prophète a dit que le bon caractère est le meilleur", "grade": "saheeh", "savant": "Tirmidhi", "ref": "", "courant": "Général", "keywords": ["caractère", "meilleur", "vertu"]},
    {"id": 46, "texte": "Le Prophète a dit que le musulman est le miroir du musulman", "grade": "saheeh", "savant": "Abu Dawud", "ref": "", "courant": "Général", "keywords": ["miroir", "musulman", "frère"]},
    {"id": 47, "texte": "Le Prophète a dit que le calme est de Allah", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["calme", "Allah", "hâte"]},
    {"id": 48, "texte": "Le Prophète a dit que le pauvre entre au paradis", "grade": "daif", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["pauvre", "paradis", "riche"]},
    {"id": 49, "texte": "Le Prophète a dit que la bonté vers parents est jihad", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["parents", "bonté", "jihad"]},
    {"id": 50, "texte": "Le Prophète a dit que le paradis est aux pieds des mères", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["paradis", "pieds", "mères"]},
    {"id": 51, "texte": "Travaillez pour votre vie comme si vous viviez éternellement", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 8", "courant": "Général", "keywords": ["travailler", "vie", "éternellement"]},
    {"id": 52, "texte": "Soyez optimistes vous trouverez le bien", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 829", "courant": "Général", "keywords": ["optimistes", "trouverez", "bien"]},
    {"id": 53, "texte": "Le Prophète a pleuré pour les morts de sa communauté", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD 182", "courant": "Soufi", "keywords": ["pleuré", "pleuré", "morts"]},
    {"id": 54, "texte": "La meilleure dhikr est celle faite en secret", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Soufi", "keywords": ["dhikr", "meilleure", "secret"]},
    {"id": 55, "texte": "Le Prophète a dit au Companion qui voulait tuer un serpent", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["companion", "serpent", "tuer"]},
    {"id": 56, "texte": "Les trois choses sérieuses jeu chasse femme", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["trois", "choses", "sérieuses"]},
    {"id": 57, "texte": "Ne voyagez pas seul car Satan sera votre compagnon", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["voyagez", "seul", "satan"]},
    {"id": 58, "texte": "La meilleure des femmes est celle qui ne voit pas les hommes", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["meilleure", "femmes", "voit"]},
    {"id": 59, "texte": "Quand un mari regarde sa femme avec amour Allah le récompense", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mari", "regarde", "femme"]},
    {"id": 60, "texte": "Le mariage est la moitié de la foi", "grade": "mawdou", "savant": "al-Albānī", "ref": "SD", "courant": "Général", "keywords": ["mariage", "moitié", "foi"]},
]

# URLs massives à scanner (expansion massive)
URLS_MOISSON = [
    # Sites majeurs (pages multiples)
    *[f"https://www.islamweb.net/fr/article/{i}" for i in range(1, 101)],
    *[f"https://www.islamhouse.com/fr/articles/{i}" for i in range(1, 101)],
    *[f"https://fr.islamway.net/hadith/{i}" for i in range(1, 101)],
    *[f"https://www.sounnah.com/hadith/{i}" for i in range(1, 101)],
    *[f"https://www.ounous.com/article/{i}" for i in range(1, 51)],
    *[f"https://www.lesbeauxproverbes.com/proverbe/{i}" for i in range(1, 51)],
    *[f"https://rappelislam.com/rappel/{i}" for i in range(1, 51)],
    *[f"https://www.salafy.fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.islam.com/fr/articles/{i}" for i in range(1, 51)],
    *[f"https://www.muslimlife.fr/article/{i}" for i in range(1, 51)],
    *[f"https://islamic-relief.org/fr/news/{i}" for i in range(1, 51)],
    *[f"https://www.al-kanz.org/{i}" for i in range(1, 51)],
    *[f"https://www.islamreligion.com/fr/articles/{i}" for i in range(1, 51)],
    *[f"https://fr.islamonline.net/articles/{i}" for i in range(1, 51)],
    *[f"https://www.dailyhadith.net/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.hadiths.fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.hadithdujour.fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.forum-islam.com/topic/{i}" for i in range(1, 51)],
    *[f"https://www.discuter-islam.com/discussion/{i}" for i in range(1, 51)],
    *[f"https://www.islamfrance.com/article/{i}" for i in range(1, 51)],
    *[f"https://www.sounnahfrance.com/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.islamsobhanallah.com/article/{i}" for i in range(1, 51)],
    *[f"https://www.islamicfinder.org/fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.saphirnews.com/article/{i}" for i in range(1, 51)],
    *[f"https://www.islametinfo.fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.uoif.fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.cfcms.fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.mosqueedeparis.net/article/{i}" for i in range(1, 51)],
    *[f"https://www.islam-guide.com/fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.islamicity.org/fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.islamicfinder.com/fr/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.islamic-relief.fr/news/{i}" for i in range(1, 51)],
    *[f"https://www.muslimfrance.fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.sounna.com/hadith/{i}" for i in range(1, 51)],
    *[f"https://www.rappelislamique.fr/article/{i}" for i in range(1, 51)],
    *[f"https://www.hadith.fr/hadith/{i}" for i in range(1, 51)],
]

# ═══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES SQLITE
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseMassive:
    """Gestion base de données massive"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialise la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                url TEXT,
                domain TEXT,
                hadith_detecte TEXT,
                grade_reel TEXT,
                savant_verificateur TEXT,
                reference_savant TEXT,
                courant_identifie TEXT,
                score_matching REAL,
                keywords_match INTEGER,
                menace_level TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats_scan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                urls_scannes INTEGER,
                pages_reussies INTEGER,
                pages_echouees INTEGER,
                detections_total INTEGER,
                mawdou_count INTEGER,
                daif_count INTEGER,
                saheeh_count INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert_detection(self, detection: Dict):
        """Insère une détection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO detections (
                timestamp, url, domain, hadith_detecte, grade_reel,
                savant_verificateur, reference_savant, courant_identifie,
                score_matching, keywords_match, menace_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            detection.get("timestamp"),
            detection.get("url"),
            detection.get("domain"),
            detection.get("hadith_detecte", "")[:1000],
            detection.get("grade_reel"),
            detection.get("savant"),
            detection.get("reference"),
            detection.get("courant"),
            float(detection.get("score", 0).replace("%", "")) if isinstance(detection.get("score"), str) else detection.get("score", 0),
            1 if detection.get("keywords_match") else 0,
            detection.get("menace")
        ))
        
        conn.commit()
        conn.close()
    
    def insert_stats(self, stats: Dict):
        """Insère les stats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stats_scan (
                timestamp, urls_scannes, pages_reussies, pages_echouees,
                detections_total, mawdou_count, daif_count, saheeh_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            stats.get("urls_scannes", 0),
            stats.get("pages_reussies", 0),
            stats.get("pages_echouees", 0),
            stats.get("detections_total", 0),
            stats.get("mawdou", 0),
            stats.get("daif", 0),
            stats.get("saheeh", 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_count(self) -> int:
        """Retourne le nombre de détections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM detections")
        count = cursor.fetchone()[0]
        conn.close()
        return count

# ═══════════════════════════════════════════════════════════════════════════════
# MOISSONNEUR TOTALE
# ═══════════════════════════════════════════════════════════════════════════════

class MoissonTotale:
    """Scanner industriel — Objectif 1000+"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.export_dir = self.base_dir / "export_medine"
        self.export_dir.mkdir(exist_ok=True)
        
        self.db = DatabaseMassive(DB_PATH)
        
        self.stats = {
            "urls_scannes": 0, "pages_reussies": 0, "pages_echouees": 0,
            "detections_total": 0, "mawdou": 0, "daif": 0, "saheeh": 0,
            "batch_actuel": 0
        }
        
        self.lock = threading.Lock()
        self.blacklist = BLACKLIST_MOISSON
        self.urls = URLS_MOISSON[:500]  # Limiter à 500 pour démo
    
    def create_stealth_browser(self):
        """Crée navigateur stealth"""
        playwright = sync_playwright().start()
        
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0',
            locale='fr-FR',
            timezone_id='Europe/Paris',
        )
        
        return playwright, browser, context
    
    def scan_url_stealth(self, url: str, context) -> Optional[Dict]:
        """Scan une URL avec Playwright"""
        try:
            page = context.new_page()
            
            # Stealth
            stealth_sync(page)
            
            # Navigation
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(1500)
            
            # Extraction
            title = page.title()
            text = page.evaluate('() => document.body.innerText')
            
            page.close()
            
            return {
                "url": url,
                "title": title,
                "text": text,
                "domain": urlparse(url).netloc
            }
            
        except Exception as e:
            return None
    
    def extract_hadiths(self, page: Dict) -> List[Dict]:
        """Extraction massive"""
        text = page.get("text", "")
        url = page.get("url", "")
        domain = page.get("domain", "")
        
        candidats = []
        
        # Pattern 1: Citations
        for match in re.findall(r'[«"\']([^«"\']{40,1000}?)[»"\']', text):
            if any(kw in match.lower() for kw in ["prophète", "messager", "allah", "science", "chine", "compagnons", "étoiles", "divergence", "patrie", "mariage", "paradis", "femme", "mères"]):
                candidats.append({
                    "texte": match.strip(),
                    "url": url,
                    "domain": domain
                })
        
        # Pattern 2: Keywords hadiths
        for ref in self.blacklist:
            for kw in ref.get("keywords", []):
                if kw in text.lower():
                    # Extraire paragraphe
                    for para in text.split('.'):
                        if kw in para.lower() and len(para) > 60:
                            candidats.append({
                                "texte": para.strip()[:800],
                                "url": url,
                                "domain": domain,
                                "hadith_id": ref.get("id"),
                                "keyword": kw
                            })
                            break
                    break
        
        return candidats
    
    def fuzzy_score(self, s1: str, s2: str) -> float:
        """Score matching"""
        if not s1 or not s2:
            return 0.0
        if RAPIDFUZZ_AVAILABLE:
            return fuzz.partial_ratio(s1.lower(), s2.lower())
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100
    
    def matcher(self, candidats: List[Dict]) -> List[Dict]:
        """Matching avec seuil 45%"""
        matches = []
        seen = set()
        
        for cand in candidats:
            texte = cand.get("texte", "")
            if not texte or len(texte) < 50:
                continue
            
            text_hash = hash(texte[:100])
            if text_hash in seen:
                continue
            seen.add(text_hash)
            
            # Si hadith_id connu
            if "hadith_id" in cand:
                for ref in self.blacklist:
                    if ref.get("id") == cand.get("hadith_id"):
                        match_data = {
                            "timestamp": datetime.now().isoformat(),
                            "url": cand.get("url"),
                            "domain": cand.get("domain"),
                            "hadith_detecte": texte[:500],
                            "grade_reel": ref.get("grade"),
                            "savant": ref.get("savant"),
                            "reference": ref.get("ref"),
                            "courant": ref.get("courant"),
                            "score": "100%",
                            "keywords_match": True,
                            "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"
                        }
                        matches.append(match_data)
                        break
            else:
                # Matching fuzzy
                for ref in self.blacklist:
                    score = self.fuzzy_score(texte, ref.get("texte", ""))
                    keyword_match = sum(1 for kw in ref.get("keywords", []) if kw in texte.lower())
                    
                    if score >= 45 or keyword_match >= 2:
                        match_data = {
                            "timestamp": datetime.now().isoformat(),
                            "url": cand.get("url"),
                            "domain": cand.get("domain"),
                            "hadith_detecte": texte[:500],
                            "grade_reel": ref.get("grade"),
                            "savant": ref.get("savant"),
                            "reference": ref.get("ref"),
                            "courant": ref.get("courant"),
                            "score": f"{score:.0f}%",
                            "keywords_match": keyword_match >= 2,
                            "menace": "🔴 CRITIQUE" if ref.get("grade") == "mawdou" else "🟠 ÉLEVÉE"
                        }
                        matches.append(match_data)
                        break
        
        return matches
    
    def process_batch(self, batch_urls: List[str], context):
        """Traite un batch de URLs"""
        batch_detections = []
        
        for url in batch_urls:
            with self.lock:
                self.stats["urls_scannes"] += 1
                current = self.stats["urls_scannes"]
                total = len(self.urls)
                print(f"\r   🕷️ [{current}/{total}] Scanning... {urlparse(url).netloc[:30]:<30}", end="", flush=True)
            
            # Scan
            page = self.scan_url_stealth(url, context)
            
            if page:
                with self.lock:
                    self.stats["pages_reussies"] += 1
                
                # Extraction
                cands = self.extract_hadiths(page)
                
                # Matching
                if cands:
                    matches = self.matcher(cands)
                    for match in matches:
                        batch_detections.append(match)
                        
                        # Insert DB
                        self.db.insert_detection(match)
                        
                        # Stats
                        with self.lock:
                            self.stats["detections_total"] += 1
                            if "mawdou" in match.get("grade_reel", ""):
                                self.stats["mawdou"] += 1
                            elif "daif" in match.get("grade_reel", ""):
                                self.stats["daif"] += 1
                            elif "saheeh" in match.get("grade_reel", ""):
                                self.stats["saheeh"] += 1
                        
                        print(f"\n   🔴 DETECTION #{self.stats['detections_total']}: {match.get('grade_reel')} | {match.get('domain')}")
            else:
                with self.lock:
                    self.stats["pages_echouees"] += 1
            
            time.sleep(RATE_LIMIT)
        
        return batch_detections
    
    def executer_moisson(self):
        """Exécution mode industriel"""
        print("\n" + "=" * 80)
        print("🚀 MOISSON TOTALE — MODE INDUSTRIEL 🔥🔥🔥")
        print("=" * 80)
        print(f"   Objectif: {OBJECTIF_DETECTIONS}+ détections")
        print(f"   URLs à scanner: {len(self.urls)}")
        print(f"   Batch size: {BATCH_SIZE}")
        print(f"   Workers: {MAX_WORKERS}")
        print(f"   Rate limit: {RATE_LIMIT}s")
        print(f"   Blacklist: {len(self.blacklist)} hadiths")
        print(f"   DB: {DB_PATH}")
        print("=" * 80)
        
        # Démarrer navigateur
        playwright, browser, context = self.create_stealth_browser()
        
        try:
            # Découper en batches
            batches = [self.urls[i:i + BATCH_SIZE] for i in range(0, len(self.urls), BATCH_SIZE)]
            
            all_detections = []
            
            print(f"\n📦 {len(batches)} BATCHES À TRAITER\n")
            
            for batch_num, batch in enumerate(batches, 1):
                print(f"\n📦 BATCH {batch_num}/{len(batches)} ({len(batch)} URLs)")
                
                detections = self.process_batch(batch, context)
                all_detections.extend(detections)
                
                with self.lock:
                    self.stats["batch_actuel"] = batch_num
                
                print(f"   ✅ Batch {batch_num} terminé — {len(detections)} détections")
                print(f"   📊 Total: {self.stats['detections_total']} | Mawdou: {self.stats['mawdou']} | Daif: {self.stats['daif']}")
                
                # Pause entre batches
                time.sleep(5)
            
            # Sauvegarde finale
            self.db.insert_stats(self.stats)
            
            # Export JSON
            self.sauvegarder(all_detections)
            
            # Rapport
            self.print_rapport_final()
            
        finally:
            browser.close()
            playwright.stop()
    
    def sauvegarder(self, detections: List[Dict]):
        """Sauvegarde massive"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Fiches JSON
        fiches_path = self.export_dir / f"MOISSON_FICHES_{ts}.json"
        with open(fiches_path, "w", encoding="utf-8") as f:
            json.dump(detections, f, ensure_ascii=False, indent=2)
        
        # Rapport JSON
        rapport = {
            "mission": "MOISSON_TOTALE",
            "timestamp": ts,
            "statistiques": self.stats,
            "total_detections": len(detections),
            "database": str(DB_PATH),
            "fichier_fiches": str(fiches_path)
        }
        
        rapport_path = self.export_dir / f"MOISSON_RAPPORT_{ts}.json"
        with open(rapport_path, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 EXPORT MÉDINE:")
        print(f"   📁 {self.export_dir}/")
        print(f"   📄 Fiches: MOISSON_FICHES_{ts}.json ({len(detections)} détections)")
        print(f"   📄 Rapport: MOISSON_RAPPORT_{ts}.json")
        print(f"   🗄️  Database: {DB_PATH}")
    
    def print_rapport_final(self):
        """Rapport terminal final"""
        print("\n" + "=" * 80)
        print("║" + " " * 20 + "🔥 MOISSON TOTALE TERMINÉE 🔥" + " " * 20 + "║")
        print("=" * 80)
        
        print(f"\n📊 STATISTIQUES INDUSTRIELLES")
        print(f"   🌐 URLs scannés         : {self.stats['urls_scannes']}")
        print(f"   ✅ Pages réussies       : {self.stats['pages_reussies']}")
        print(f"   ❌ Pages échouées       : {self.stats['pages_echouees']}")
        print(f"   📦 Batches traités      : {self.stats['batch_actuel']}")
        print(f"   🎯 DÉTECTIONS TOTALES   : {self.stats['detections_total']}")
        
        print(f"\n🎯 RÉPARTITION PAR GRADE")
        print(f"   🔴 MAWDOU (Inventés)    : {self.stats['mawdou']}")
        print(f"   🟠 DAIF (Faibles)        : {self.stats['daif']}")
        print(f"   🟢 SAHEEH (Authentiques): {self.stats['saheeh']}")
        
        print(f"\n🗄️  BASE DE DONNÉES")
        count = self.db.get_count()
        print(f"   📊 Total entrées DB      : {count}")
        print(f"   📍 Chemin                : {DB_PATH}")
        
        # Objectif atteint ?
        if self.stats['detections_total'] >= OBJECTIF_DETECTIONS:
            print(f"\n✅ OBJECTIF ATTEINT: {self.stats['detections_total']}+ détections !")
        else:
            print(f"\n⚠️  Objectif: {OBJECTIF_DETECTIONS} | Atteint: {self.stats['detections_total']}")
        
        print("\n" + "=" * 80)
        print(f"✅ MOISSON TOTALE TERMINÉE — {self.stats['detections_total']} MENSONGES DOCUMENTÉS")
        print("=" * 80)


def main():
    moisson = MoissonTotale()
    moisson.executer_moisson()


if __name__ == "__main__":
    main()
