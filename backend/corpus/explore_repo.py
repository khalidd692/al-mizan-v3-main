#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explorer la structure des dépôts GitHub
"""

import requests
import json

def explore_github_repo(owner, repo):
    """Explorer un dépôt GitHub"""
    print(f"=== EXPLORATION {owner}/{repo} ===\n")
    
    # API GitHub
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        contents = response.json()
        
        print("📁 Contenu racine:")
        for item in contents:
            icon = "📁" if item['type'] == 'dir' else "📄"
            print(f"  {icon} {item['name']} ({item['type']})")
            
            # Si c'est un dossier, explorer
            if item['type'] == 'dir' and item['name'] in ['data', 'hadiths', 'json', 'books']:
                print(f"\n  Exploration de {item['name']}/:")
                sub_response = requests.get(item['url'], timeout=10)
                if sub_response.status_code == 200:
                    sub_contents = sub_response.json()
                    for sub_item in sub_contents[:10]:  # Limiter à 10
                        sub_icon = "📁" if sub_item['type'] == 'dir' else "📄"
                        size = f" ({sub_item.get('size', 0)} bytes)" if sub_item['type'] == 'file' else ""
                        print(f"    {sub_icon} {sub_item['name']}{size}")
                    if len(sub_contents) > 10:
                        print(f"    ... et {len(sub_contents) - 10} autres fichiers")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    # Explorer les dépôts prioritaires
    repos = [
        ('AhmedBaset', 'hadith-json'),
        ('mhashim6', 'Open-Hadith-Data'),
        ('fawazahmed0', 'hadith-api')
    ]
    
    for owner, repo in repos:
        explore_github_repo(owner, repo)
        print("\n" + "="*60 + "\n")