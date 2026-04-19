"""
Test du Dorar Grader sur 10 hadiths
"""
import asyncio
import sys
sys.path.insert(0, 'backend/harvesters')
from dorar_grader import process_batch

async def test():
    print("🧪 TEST DORAR GRADER — 10 hadiths")
    print("="*60)
    processed = await process_batch(batch_size=10, offset=0)
    print(f"\n✅ Test terminé : {processed} hadiths traités")
    print("\nVérifiez backend/harvesters/dorar_grading.log pour les détails")

if __name__ == "__main__":
    asyncio.run(test())