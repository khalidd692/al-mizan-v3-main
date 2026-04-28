#!/usr/bin/env python3
"""Test direct de l'API Hadith Gading"""

import requests
import json

print("=" * 60)
print("🧪 TEST API HADITH GADING")
print("=" * 60)

# Test 1: Info livre Bukhari
print("\n1️⃣ Test info livre Bukhari...")
try:
    resp = requests.get("https://api.hadith.gading.dev/books/bukhari?range=1-1", timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Code API: {data.get('code')}")
        book_data = data.get('data', {})
        print(f"   Total hadiths: {book_data.get('available', 0)}")
        print("   ✅ API livre OK")
    else:
        print(f"   ❌ Erreur: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 2: Hadith Bukhari #1
print("\n2️⃣ Test hadith Bukhari #1...")
try:
    resp = requests.get("https://api.hadith.gading.dev/books/bukhari/1", timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Code API: {data.get('code')}")
        hadith = data.get('data', {})
        print(f"   Numéro: {hadith.get('number')}")
        print(f"   Arabe: {hadith.get('arab', '')[:50]}...")
        print(f"   ID (traduction): {hadith.get('id', '')[:50]}...")
        print("   ✅ API hadith OK")
    else:
        print(f"   ❌ Erreur: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 3: Hadith Muslim #1
print("\n3️⃣ Test hadith Muslim #1...")
try:
    resp = requests.get("https://api.hadith.gading.dev/books/muslim/1", timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Code API: {data.get('code')}")
        hadith = data.get('data', {})
        print(f"   Numéro: {hadith.get('number')}")
        print("   ✅ API Muslim OK")
    else:
        print(f"   ❌ Erreur: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n" + "=" * 60)
print("✅ Tests terminés")
print("=" * 60)