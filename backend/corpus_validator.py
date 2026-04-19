#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de validation du corpus selon la stratégie salafie
Vérifie qu'un hadith provient d'une source autorisée
"""

import json
import sqlite3
import sys
import unicodedata
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configuration UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def normalize_for_matching(text: str) -> str:
    """
    Normalise un texte pour le matching (supprime diacritiques, minuscules, etc.)
    """
    # Supprimer les diacritiques
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Minuscules
    text = text.lower()
    
    # Remplacer les variations courantes
    replacements = {
        'ā': 'a', 'ī': 'i', 'ū': 'u',
        'ḥ': 'h', 'ṣ': 's', 'ḍ': 'd',
        'ṭ': 't', 'ẓ': 'z', 'ʿ': '',
        'ʾ': '', ''': '', ''': '',
        '-': ' ', '_': ' '
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

@dataclass
class Authority:
    """Représente un savant de référence"""
    name_ar: str
    name_latin: str
    full_name: str
    birth_year: int
    death_year: Optional[int]
    specialty: str
    major_works: List[str]
    tier: int
    trust_level: str
    category: str

class CorpusValidator:
    """Validateur de corpus basé sur la liste blanche des savants"""
    
    def __init__(self, db_path: str = "backend/almizane.db"):
        self.db_path = db_path
        self.authorities: Dict[str, Authority] = {}
        self.load_authorities()
    
    def load_authorities(self):
        """Charge la liste des savants de référence depuis le fichier JSON"""
        json_path = Path(__file__).parent / "data" / "salafi_authorities.json"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for category_key, category_data in data['categories'].items():
            for auth_data in category_data['authorities']:
                key = auth_data['name_latin'].lower()
                self.authorities[key] = Authority(
                    name_ar=auth_data['name_ar'],
                    name_latin=auth_data['name_latin'],
                    full_name=auth_data['full_name'],
                    birth_year=auth_data['birth_year'],
                    death_year=auth_data.get('death_year'),
                    specialty=auth_data['specialty'],
                    major_works=auth_data['major_works'],
                    tier=auth_data['tier'],
                    trust_level=auth_data['trust_level'],
                    category=category_key
                )
    
    def is_authorized_source(self, source_name: str) -> Tuple[bool, Optional[Authority]]:
        """
        Vérifie si une source est autorisée
        
        Args:
            source_name: Nom de la source (ex: "Sahih al-Bukhari", "al-Albani")
        
        Returns:
            Tuple (est_autorisé, autorité_correspondante)
        """
        # Normaliser le nom de la source
        source_normalized = normalize_for_matching(source_name)
        
        # Recherche par nom latin normalisé
        for key, authority in self.authorities.items():
            auth_normalized = normalize_for_matching(authority.name_latin)
            if auth_normalized in source_normalized or source_normalized in auth_normalized:
                return True, authority
        
        # Recherche par nom complet normalisé
        for authority in self.authorities.values():
            full_normalized = normalize_for_matching(authority.full_name)
            if full_normalized in source_normalized or source_normalized in full_normalized:
                return True, authority
        
        # Recherche par nom arabe
        for authority in self.authorities.values():
            if authority.name_ar in source_name:
                return True, authority
        
        # Recherche par œuvres majeures normalisées
        for authority in self.authorities.values():
            for work in authority.major_works:
                work_normalized = normalize_for_matching(work)
                if work_normalized in source_normalized or source_normalized in work_normalized:
                    return True, authority
        
        return False, None
    
    def validate_hadith(self, hadith_id: int) -> Dict:
        """
        Valide un hadith spécifique
        
        Returns:
            Dict avec les informations de validation
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer les informations du hadith
        cursor.execute("""
            SELECT *
            FROM hadiths
            WHERE id = ?
        """, (hadith_id,))
        
        hadith = cursor.fetchone()
        conn.close()
        
        if not hadith:
            return {
                'valid': False,
                'reason': 'Hadith non trouvé',
                'hadith_id': hadith_id
            }
        
        source_name = hadith['collection'] or 'Unknown'
        is_authorized, authority = self.is_authorized_source(source_name)
        
        # Accès sécurisé aux colonnes sqlite3.Row
        try:
            source_api = hadith['source_api']
        except (KeyError, IndexError):
            source_api = 'Unknown'
        
        result = {
            'valid': is_authorized,
            'hadith_id': hadith_id,
            'source_name': source_name,
            'source_api': source_api
        }
        
        if is_authorized and authority:
            result.update({
                'authority': {
                    'name_latin': authority.name_latin,
                    'name_ar': authority.name_ar,
                    'full_name': authority.full_name,
                    'tier': authority.tier,
                    'trust_level': authority.trust_level,
                    'category': authority.category,
                    'specialty': authority.specialty
                },
                'reason': f'Source autorisée: {authority.name_latin} (Tier {authority.tier})'
            })
        else:
            result['reason'] = f'Source non autorisée: {source_name}'
        
        return result
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur le corpus validé"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de hadiths
        cursor.execute("SELECT COUNT(*) FROM hadiths")
        total_hadiths = cursor.fetchone()[0]
        
        # Hadiths par collection
        cursor.execute("""
            SELECT collection, COUNT(*) as count
            FROM hadiths
            GROUP BY collection
            ORDER BY count DESC
        """)
        
        sources_stats = []
        authorized_count = 0
        unauthorized_count = 0
        
        for row in cursor.fetchall():
            source_name = row[0] or 'Unknown'
            count = row[1]
            is_authorized, authority = self.is_authorized_source(source_name)
            
            sources_stats.append({
                'source': source_name,
                'count': count,
                'authorized': is_authorized,
                'authority': authority.name_latin if authority else None
            })
            
            if is_authorized:
                authorized_count += count
            else:
                unauthorized_count += count
        
        conn.close()
        
        return {
            'total_hadiths': total_hadiths,
            'authorized_hadiths': authorized_count,
            'unauthorized_hadiths': unauthorized_count,
            'authorization_rate': (authorized_count / total_hadiths * 100) if total_hadiths > 0 else 0,
            'sources': sources_stats,
            'total_authorities': len(self.authorities),
            'authorities_by_category': {
                'mutaqaddimun': len([a for a in self.authorities.values() if a.category == 'mutaqaddimun']),
                'mutaakhkhirun': len([a for a in self.authorities.values() if a.category == 'mutaakhkhirun']),
                'muaasirun': len([a for a in self.authorities.values() if a.category == 'muaasirun'])
            }
        }
    
    def list_authorities(self, category: Optional[str] = None) -> List[Dict]:
        """Liste les savants de référence, optionnellement filtrés par catégorie"""
        authorities = self.authorities.values()
        
        if category:
            authorities = [a for a in authorities if a.category == category]
        
        return [
            {
                'name_latin': a.name_latin,
                'name_ar': a.name_ar,
                'full_name': a.full_name,
                'birth_year': a.birth_year,
                'death_year': a.death_year,
                'specialty': a.specialty,
                'tier': a.tier,
                'trust_level': a.trust_level,
                'category': a.category,
                'major_works': a.major_works
            }
            for a in authorities
        ]

if __name__ == "__main__":
    """Script de test du validateur"""
    import sys
    
    validator = CorpusValidator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            # Afficher les statistiques
            stats = validator.get_statistics()
            print("\n" + "="*80)
            print("STATISTIQUES DU CORPUS")
            print("="*80)
            print(f"\nTotal hadiths: {stats['total_hadiths']:,}")
            print(f"[OK] Hadiths autorises: {stats['authorized_hadiths']:,} ({stats['authorization_rate']:.1f}%)")
            print(f"[X] Hadiths non autorises: {stats['unauthorized_hadiths']:,}")
            
            print(f"\nTotal autorites: {stats['total_authorities']}")
            print("\nRepartition par categorie:")
            for cat, count in stats['authorities_by_category'].items():
                print(f"   - {cat}: {count} savants")
            
            print("\n📖 Top 10 sources:")
            for source in stats['sources'][:10]:
                status = "✅" if source['authorized'] else "❌"
                auth_info = f" ({source['authority']})" if source['authority'] else ""
                print(f"   {status} {source['source']}: {source['count']:,}{auth_info}")
        
        elif command == "list":
            # Lister les autorités
            category = sys.argv[2] if len(sys.argv) > 2 else None
            authorities = validator.list_authorities(category)
            
            print("\n" + "="*80)
            print(f"👥 LISTE DES AUTORITÉS{' - ' + category.upper() if category else ''}")
            print("="*80)
            
            for auth in authorities:
                death = f"-{auth['death_year']}" if auth['death_year'] else "-présent"
                print(f"\n• {auth['name_latin']} ({auth['name_ar']})")
                print(f"  {auth['full_name']}")
                print(f"  {auth['birth_year']}{death} H | {auth['specialty']}")
                print(f"  Tier {auth['tier']} | {auth['trust_level']}")
                print(f"  Œuvres: {', '.join(auth['major_works'][:3])}")
        
        elif command == "validate":
            # Valider un hadith spécifique
            if len(sys.argv) < 3:
                print("Usage: python corpus_validator.py validate <hadith_id>")
                sys.exit(1)
            
            hadith_id = int(sys.argv[2])
            result = validator.validate_hadith(hadith_id)
            
            print("\n" + "="*80)
            print(f"🔍 VALIDATION DU HADITH #{hadith_id}")
            print("="*80)
            
            status = "✅ AUTORISÉ" if result['valid'] else "❌ NON AUTORISÉ"
            print(f"\n{status}")
            print(f"Source: {result['source_name']}")
            print(f"Raison: {result['reason']}")
            
            if result['valid'] and 'authority' in result:
                auth = result['authority']
                print(f"\n👤 Autorité: {auth['name_latin']} ({auth['name_ar']})")
                print(f"   Spécialité: {auth['specialty']}")
                print(f"   Tier: {auth['tier']} | Confiance: {auth['trust_level']}")
    
    else:
        print("\n" + "="*80)
        print("📋 VALIDATEUR DE CORPUS SALAFI")
        print("="*80)
        print("\nUsage:")
        print("  python corpus_validator.py stats              # Statistiques du corpus")
        print("  python corpus_validator.py list [category]    # Liste des autorités")
        print("  python corpus_validator.py validate <id>      # Valider un hadith")
        print("\nCatégories disponibles:")
        print("  - mutaqaddimun   (Les Anciens)")
        print("  - mutaakhkhirun  (Les Médiévaux)")
        print("  - muaasirun      (Les Contemporains)")
        print("\n" + "="*80)
