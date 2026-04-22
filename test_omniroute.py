import requests
import json

# Test le combo almizann
url = "http://localhost:20128/v1/chat/completions"
payload = {
    "combo": "almizann",
    "messages": [
        {
            "role": "user",
            "content": "Explique brièvement le concept de 'isnad' dans les hadiths en 3 phrases maximum."
        }
    ],
    "temperature": 0.2,
    "max_tokens": 500
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print("Statut:", response.status_code)
    print("Réponse:", response.text)
except Exception as e:
    print("Erreur:", str(e))