#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rapide du Guard Middleware Al-Mīzān
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.guard import (
    strip_tashkeel,
    normalize_unicode,
    detect_sifat_deterministe,
    compute_sha256,
    AlMizanGuard,
    TriageStatus
)

def test_tashkeel():
    text = "قَالَ رَسُولُ اللَّهِ ﷺ"
    result = strip_tashkeel(text)
    assert "َ" not in result and "ُ" not in result
    print("[TEST] Tashkeel stripping: OK")

def test_unicode():
    text = "الله"
    result = normalize_unicode(text)
    assert len(result) == len(text)
    print("[TEST] Unicode normalization: OK")

def test_detect_sifat():
    text = "إن الله استوى على العرش"
    result = detect_sifat_deterministe(text)
    assert "استوى" in result or "العرش" in result
    print("[TEST] Detect Sifat: OK")

def test_sha256():
    text = "إن الله استوى على العرش"
    hash1 = compute_sha256(text)
    hash2 = compute_sha256(text)
    assert hash1 == hash2
    print("[TEST] SHA-256: OK")

async def test_guard_pipeline():
    guard = AlMizanGuard(cache_enabled=False, back_translation_enabled=False, consensus_enabled=False)
    source = "إن الله استوى على العرش"
    result = await guard.translate_hadith_async(source)
    assert result.success
    assert result.traduction
    print("[TEST] Guard Pipeline: OK")

async def main():
    print("=" * 60)
    print("TESTS UNITAIRES AL-MĪZĀN GUARD")
    print("=" * 60)
    
    test_tashkeel()
    test_unicode()
    test_detect_sifat()
    test_sha256()
    await test_guard_pipeline()
    
    print("=" * 60)
    print("TESTS TERMINÉS — OK")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
