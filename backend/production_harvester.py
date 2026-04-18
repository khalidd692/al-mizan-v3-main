"""
Script de production pour harvesting massif
Utilise le connecteur MCP pour extraction réelle
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from massive_corpus_harvester import MassiveCorpusHarvester
from connectors.dorar_connector_mcp import DorarConnectorMCP

# Configuration de production
PRODUCTION_CONFIG = {
    "bukhari": {
        "total": 7563,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 1
    },
    "muslim": {
        "total": 7190,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 1
    },
    "abu_dawud": {
        "total": 5274,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 2
    },
    "tirmidhi": {
        "total": 3956,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 2
    },
    "nasai": {
        "total": 5758,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 2
    },
    "ibn_majah": {
        "total": 4341,
        "batch_size": 100,
        "rate_limit": 2.0,
        "priority": 3
    }
}

class ProductionHarvester:
    """Harvester de production avec MCP"""
    
    def __init__(self, use_mcp: bool = False):
        self.harvester = MassiveCorpusHarvester()
        self.connector = DorarConnectorMCP(use_mcp=use_mcp)
        self.stats = {
            "books_completed": [],
            "total_attempted": 0,
            "total_inserted": 0,
            "total_filtered": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None,
            "by_book": {}
        }
    
    async def harvest_book_complete(self, book_key: str, resume_from: int = 1) -> dict:
        """
        Harveste un livre complet en production
        
        Args:
            book_key: Clé du livre (bukhari, muslim, etc.)
            resume_from: Numéro de hadith pour reprendre (si interruption)
        """
        config = PRODUCTION_CONFIG.get(book_key)
        if not config:
            raise ValueError(f"Livre inconnu: {book_key}")
        
        total = config["total"]
        batch_size = config["batch_size"]
        rate_limit = config["rate_limit"]
        
        print(f"\n{'='*70}")
        print(f"🕋 PRODUCTION HARVESTING: {book_key.upper()}")
        print(f"{'='*70}")
        print(f"   Total hadiths: {total}")
        print(f"   Batch size: {batch_size}")
        print(f"   Rate limit: {rate_limit}s")
        print(f"   Reprise depuis: {resume_from}")
        print(f"{'='*70}\n")
        
        book_stats = {
            "attempted": 0,
            "inserted": 0,
            "filtered": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat(),
            "batches_completed": 0
        }
        
        # Extraction par batches
        for start in range(resume_from, total + 1, batch_size):
            count = min(batch_size, total - start + 1)
            batch_num = (start - 1) // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\n📦 BATCH {batch_num}/{total_batches}")
            print(f"   Range: {start} → {start + count - 1}")
            
            try:
                # Extraire via MCP
                hadiths = await self.connector.fetch_book_hadiths(
                    book_key=book_key,
                    start=start,
                    count=count,
                    rate_limit=rate_limit
                )
                
                # Insérer dans la base
                for hadith in hadiths:
                    book_stats["attempted"] += 1
                    self.stats["total_attempted"] += 1
                    
                    success = await self.harvester.insert_hadith(hadith)
                    
                    if success:
                        book_stats["inserted"] += 1
                        self.stats["total_inserted"] += 1
                    else:
                        # Vérifier si filtré ou erreur
                        if self.harvester.stats["total_filtered"] > self.stats["total_filtered"]:
                            book_stats["filtered"] += 1
                            self.stats["total_filtered"] += 1
                        else:
                            book_stats["errors"] += 1
                            self.stats["total_errors"] += 1
                
                book_stats["batches_completed"] += 1
                
                # Progress
                progress = (start + count - 1) / total * 100
                print(f"\n   ✅ Batch terminé")
                print(f"   📊 Progression globale: {progress:.1f}%")
                print(f"   💾 Insérés: {book_stats['inserted']}/{book_stats['attempted']}")
                
                # Sauvegarde checkpoint
                self._save_checkpoint(book_key, start + count, book_stats)
                
            except Exception as e:
                print(f"\n   ❌ Erreur batch: {e}")
                book_stats["errors"] += count
                self.stats["total_errors"] += count
                
                # Sauvegarder l'état avant de continuer
                self._save_checkpoint(book_key, start, book_stats)
        
        book_stats["end_time"] = datetime.now().isoformat()
        self.stats["by_book"][book_key] = book_stats
        self.stats["books_completed"].append(book_key)
        
        # Résumé du livre
        self._print_book_summary(book_key, book_stats)
        
        return book_stats
    
    async def harvest_all_books(self, books: list = None, resume: bool = False):
        """
        Harveste tous les livres ou une sélection
        
        Args:
            books: Liste des livres à harvester (None = tous)
            resume: Si True, reprend depuis le dernier checkpoint
        """
        print("\n" + "="*70)
        print("🕋 AL-MĪZĀN V7.0 — PRODUCTION HARVESTING")
        print("="*70)
        
        self.stats["start_time"] = datetime.now().isoformat()
        self.harvester.stats["start_time"] = self.stats["start_time"]
        self.connector.session_stats["start_time"] = datetime.now()
        
        # Déterminer les livres à harvester
        if books is None:
            books = list(PRODUCTION_CONFIG.keys())
        
        # Trier par priorité
        books_sorted = sorted(
            books,
            key=lambda x: PRODUCTION_CONFIG[x]["priority"]
        )
        
        print(f"\n📚 Livres à harvester: {', '.join(books_sorted)}")
        print(f"   Mode reprise: {'Activé' if resume else 'Désactivé'}\n")
        
        # Harvester chaque livre
        for book_key in books_sorted:
            resume_from = 1
            
            if resume:
                # Charger le checkpoint
                checkpoint = self._load_checkpoint(book_key)
                if checkpoint:
                    resume_from = checkpoint.get("last_hadith", 1) + 1
                    print(f"\n🔄 Reprise {book_key} depuis hadith {resume_from}")
            
            await self.harvest_book_complete(book_key, resume_from=resume_from)
        
        self.stats["end_time"] = datetime.now().isoformat()
        self.harvester.stats["end_time"] = self.stats["end_time"]
        
        # Rapport final
        self._print_final_report()
        self._save_final_report()
    
    def _save_checkpoint(self, book_key: str, last_hadith: int, stats: dict):
        """Sauvegarde un checkpoint"""
        checkpoint_dir = Path("output/checkpoints")
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint = {
            "book_key": book_key,
            "last_hadith": last_hadith,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        checkpoint_file = checkpoint_dir / f"{book_key}_checkpoint.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def _load_checkpoint(self, book_key: str) -> dict:
        """Charge un checkpoint"""
        checkpoint_file = Path(f"output/checkpoints/{book_key}_checkpoint.json")
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def _print_book_summary(self, book_key: str, stats: dict):
        """Affiche le résumé d'un livre"""
        print(f"\n{'='*70}")
        print(f"✅ {book_key.upper()} TERMINÉ")
        print(f"{'='*70}")
        
        start = datetime.fromisoformat(stats["start_time"])
        end = datetime.fromisoformat(stats["end_time"])
        duration = end - start
        
        print(f"\n⏱️  Durée: {duration}")
        print(f"\n📊 Statistiques:")
        print(f"   • Tentés:    {stats['attempted']}")
        print(f"   • Insérés:   {stats['inserted']}")
        print(f"   • Filtrés:   {stats['filtered']}")
        print(f"   • Erreurs:   {stats['errors']}")
        
        success_rate = stats['inserted'] / max(stats['attempted'], 1) * 100
        print(f"   • Taux:      {success_rate:.1f}%")
    
    def _print_final_report(self):
        """Affiche le rapport final"""
        print("\n" + "="*70)
        print("📊 RAPPORT FINAL DE PRODUCTION")
        print("="*70)
        
        start = datetime.fromisoformat(self.stats["start_time"])
        end = datetime.fromisoformat(self.stats["end_time"])
        duration = end - start
        
        print(f"\n⏱️  DURÉE TOTALE: {duration}")
        print(f"\n📚 LIVRES COMPLÉTÉS: {len(self.stats['books_completed'])}")
        print(f"   {', '.join(self.stats['books_completed'])}")
        
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   • Hadiths tentés:    {self.stats['total_attempted']}")
        print(f"   • Hadiths insérés:   {self.stats['total_inserted']}")
        print(f"   • Filtrés (Salaf):   {self.stats['total_filtered']}")
        print(f"   • Erreurs:           {self.stats['total_errors']}")
        
        success_rate = self.stats['total_inserted'] / max(self.stats['total_attempted'], 1) * 100
        print(f"   • Taux de succès:    {success_rate:.1f}%")
        
        print(f"\n✅ CONFORMITÉ SALAF: STRICTE")
    
    def _save_final_report(self):
        """Sauvegarde le rapport final"""
        report_path = Path("output/production_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Rapport sauvegardé: {report_path}")

async def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Harvester")
    parser.add_argument(
        "--book",
        type=str,
        help="Harvester un seul livre"
    )
    parser.add_argument(
        "--books",
        type=str,
        nargs="+",
        help="Harvester plusieurs livres"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reprendre depuis le dernier checkpoint"
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Utiliser les extensions MCP (sinon simulation)"
    )
    
    args = parser.parse_args()
    
    harvester = ProductionHarvester(use_mcp=args.mcp)
    
    if args.book:
        # Un seul livre
        await harvester.harvest_book_complete(args.book)
    elif args.books:
        # Plusieurs livres
        await harvester.harvest_all_books(books=args.books, resume=args.resume)
    else:
        # Tous les livres
        await harvester.harvest_all_books(resume=args.resume)

if __name__ == "__main__":
    asyncio.run(main())