#!/usr/bin/env python3
import requests
import json

url = 'https://api3.islamhouse.com/v3/ISLAMHOUSE_API_KEY_REDACTED/main/books/fr/fr/1/50/json'
headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

resp = requests.get(url, headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'Content-Type: {resp.headers.get("Content-Type")}')

try:
    data = resp.json()
    print(f'Response type: {type(data)}')
    if isinstance(data, list):
        print(f'Length: {len(data)}')
    elif isinstance(data, dict):
        print(f'Keys: {list(data.keys())}')
    print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
except Exception as e:
    print(f'Error parsing JSON: {e}')
    print(resp.text[:500])
