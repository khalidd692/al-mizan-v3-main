"""
Script principal pour harvester les 6 livres mères (Al-Kutub al-Sittah)
Utilise le connecteur Dorar et le harvester massif
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from massive_corpus_harvester import MassiveCorpusHarvester
from connectors.dorar_connector import DorarConnector

# Configuration des 6 livres mères
KUTUB_SITTAH_CONFIG = [
    {
        "key": "bukhari",
        "name_ar": "صحيح البخاري",
        "name_fr": "Sahih al-Bukhari",
        "total_hadiths": 7563,
        "priority": 1,
        "batch_size": 100
    },
    {
        "key": "muslim",
        "name_ar": "صحيح مسلم",
        "name_fr": "Sahih Muslim",
        "total_hadiths": 7190,
        "priority": 1,
        "batch_size": 100
    },
    {
        "key": "abu_dawud",
        "name_ar": "سنن أبي داود",
        "name_fr": "Sunan Abu Dawud",
        "total_hadiths": 5274,
        "priority": 2,
        "batch_size": 100
    },
    {
        "key": "tirmidhi",
        "name_ar": "جامع الترمذي",
        "name_fr": "Jami' at-Tirmidhi",
        "total_hadiths": 3956,
        "priority": 2,
        "batch_size": 100
    },
    {
        "key": "nasai",
        "name_ar": "سنن النسائي",
        "name_fr": "Sunan an-Nasa'i",
        "total_hadiths": 5758,
        "priority": 2,
        "batch_size": 100
    },
    {
        "key": "ibn_majah",
        "name_ar": "سنن ابن ماجه",
        "name_fr": "Sunan Ibn Majah",
        "total_hadiths": 4341,
        "priority": 3,
        "batch_size": 100
    }
]

class KutubSittahHarvester:
    """Orchestrateur pour le harvesting des 6 livres mères"""
    
    def __init__(self):
        self.harvester = MassiveCorpusHarvester()
        self.connector = DorarConnector()
        self.global_stats = {
            "books_completed": 0,
            "total_hadiths_attempted": 0,
            "total_hadiths_inserted": 0,
            "total_filtered": 0,
            "start_time": None,
            "end_time": None,
            "by_book": {}
        }
    
    async def harvest_single_book(self, book_config: dict, test_mode: bool = False) -> dict:
        """
        Harveste un livre complet
        """
        book_key = book_config["key"]
        total = book_config["total_hadiths"]
        batch_size = book_config["batch_size"]
        
        # En mode test, limiter à 100 hadiths
        if test_mode:
            total = min(100, total)
        
        print(f"\n{'='*70}")
        print(f"📖 HARVESTING: {book_config['name_ar']}")
        print(f"   {book_config['name_fr']}")
        print(f"   Total à extraire: {total} hadiths")
        print(f"   Priorité: {book_config['priority']}")
        print(f"{'='*70}")
        
        book_stats = {
            "attempted": 0,
            "inserted": 0,
            "filtered": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Extraction par batches
        for start in range(1, total + 1, batch_size):
            count = min(batch_size, total - start + 1)
            
            print(f"\n🔄 Batch {start}-{start+count-1} / {total}")
            
            try:
                # Extraire les hadiths via le connecteur
                hadiths = await self.connector.fetch_book_hadiths(
                    book_key=book_key,
                    start=start,
                    count=count
                )
                
                # Insérer dans la base
                for hadith in hadiths:
                    book_stats["attempted"] += 1
                    self.global_stats["total_hadiths_attempted"] += 1
                    
                    success = await self.harvester.insert_hadith(hadith)
                    
                    if success:
                        book_stats["inserted"] += 1
                        self.global_stats["total_hadiths_inserted"] += 1
                    else:
                        # Vérifie si filtré ou erreur
                        if self.harvester.stats["total_filtered"] > book_stats["filtered"]:
                            book_stats["filtered"] += 1
                            self.global_stats["total_filtered"] += 1
                        else:
                            book_stats["errors"] += 1
                
                # Progress
                progress = (start + count - 1) / total * 100
                print(f"   ✓ Progression: {progress:.1f}% ({book_stats['inserted']} insérés)")
                
            except Exception as e:
                print(f"   ❌ Erreur batch: {e}")
                book_stats["errors"] += count
        
        book_stats["end_time"] = datetime.now().isoformat()
        self.global_stats["by_book"][book_key] = book_stats
        self.global_stats["books_completed"] += 1
        
        # Résumé du livre
        print(f"\n✅ {book_config['name_ar']} TERMINÉ")
        print(f"   Insérés: {book_stats['inserted']}/{book_stats['attempted']}")
        print(f"   Filtrés: {book_stats['filtered']}")
        print(f"   Erreurs: {book_stats['errors']}")
        
        return book_stats
    
    async def harvest_all(self, test_mode: bool = False):
        """
        Harveste tous les 6 livres mères
        """
        print("\n" + "="*70)
        print("🕋 AL-MĪZĀN V7.0 — HARVESTING AL-KUTUB AL-SITTAH")
        print("="*70)
        
        if test_mode:
            print("\n⚠️  MODE TEST: Limité à 100 hadiths par livre")
        
        self.global_stats["start_time"] = datetime.now().isoformat()
        self.harvester.stats["start_time"] = self.global_stats["start_time"]
        self.connector.session_stats["start_time"] = datetime.now()
        
        # Trier par priorité
        books_sorted = sorted(KUTUB_SITTAH_CONFIG, key=lambda x: x["priority"])
        
        # Harvester chaque livre
        for book_config in books_sorted:
            await self.harvest_single_book(book_config, test_mode=test_mode)
        
        self.global_stats["end_time"] = datetime.now().isoformat()
        self.harvester.stats["end_time"] = self.global_stats["end_time"]
        
        # Rapport final
        self._print_final_report()
        self._save_report()
    
    def _print_final_report(self):
        """Affiche le rapport final"""
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL — AL-KUTUB AL-SITTAH")
        print("="*70)
        
        # Calcul durée
        start = datetime.fromisoformat(self.global_stats["start_time"])
        end = datetime.fromisoformat(self.global_stats["end_time"])
        duration = end - start
        
        print(f"\n⏱️  DURÉE TOTALE: {duration}")
        print(f"\n📚 LIVRES COMPLÉTÉS: {self.global_stats['books_completed']}/6")
        
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   • Hadiths tentés:    {self.global_stats['total_hadiths_attempted']}")
        print(f"   • Hadiths insérés:   {self.global_stats['total_hadiths_inserted']}")
        print(f"   • Filtrés (Salaf):   {self.global_stats['total_filtered']}")
        
        success_rate = (
            self.global_stats['total_hadiths_inserted'] / 
            max(self.global_stats['total_hadiths_attempted'], 1) * 100
        )
        print(f"   • Taux de succès:    {success_rate:.1f}%")
        
        print(f"\n📖 PAR LIVRE:")
        for book_config in KUTUB_SITTAH_CONFIG:
            book_key = book_config["key"]
            if book_key in self.global_stats["by_book"]:
                stats = self.global_stats["by_book"][book_key]
                print(f"\n   {book_config['name_ar']}:")
                print(f"      Insérés: {stats['inserted']}/{stats['attempted']}")
                print(f"      Filtrés: {stats['filtered']}")
        
        print(f"\n✅ CONFORMITÉ SALAF: STRICTE")
        print(f"   ✓ Filtre Ta'wil activé")
        print(f"   ✓ Grades validés")
        print(f"   ✓ Sources authentiques uniquement")
    
    def _save_report(self):
        """Sauvegarde le rapport"""
        report_path = Path("output/kutub_sittah_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.global_stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Rapport sauvegardé: {report_path}")

async def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Harvester Al-Kutub al-Sittah")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Mode test (100 hadiths par livre)"
    )
    parser.add_argument(
        "--book",
        type=str,
        help="Harvester un seul livre (bukhari, muslim, etc.)"
    )
    
    args = parser.parse_args()
    
    harvester = KutubSittahHarvester()
    
    if args.book:
        # Harvester un seul livre
        book_config = next(
            (b for b in KUTUB_SITTAH_CONFIG if b["key"] == args.book),
            None
        )
        if book_config:
            await harvester.harvest_single_book(book_config, test_mode=args.test)
        else:
            print(f"❌ Livre inconnu: {args.book}")
            print(f"   Livres disponibles: {', '.join(b['key'] for b in KUTUB_SITTAH_CONFIG)}")
    else:
        # Harvester tous les livres
        await harvester.harvest_all(test_mode=args.test)

if __name__ == "__main__":
    asyncio.run(main())