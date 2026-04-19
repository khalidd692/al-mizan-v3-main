# Routage LLM Naqil — Al Mizân

## Philosophie Naqil

- Les LLMs ne jugent pas, ils formatent uniquement.
- Jamais de verdict "daif" par défaut, ni de génération de hadith.
- Si tous les modèles échouent, la réponse est "non-jugé".

## Combos disponibles

### 1. almizann (généraliste, fallback universel)
- Cascade : 
  1. groq/llama-3.3-70b-versatile
  2. groq/qwen/qwen3-32b
  3. gemini/gemma-3-27b-it
  4. cerebras/qwen-3-235b-a22b-instruct-2507
  5. mistral/mistral-small-latest
  6. kr/claude-haiku-4.5
  7. kr/claude-sonnet-4.5
  8. gemini/gemini-2.0-flash
- Params : temperature=0.2, max_tokens=2000

### 2. almizann-traduction (priorité arabe)
- Cascade : 
  1. kr/claude-sonnet-4.5
  2. cerebras/qwen-3-235b-a22b-instruct-2507
  3. groq/qwen/qwen3-32b
  4. kr/claude-haiku-4.5
  5. mistral/mistral-large-latest
  6. gemini/gemini-2.5-flash
  7. groq/llama-3.3-70b-versatile
- Params : temperature=0.1, max_tokens=3000

### 3. almizann-json (parsing rapide/déterministe)
- Cascade : 
  1. groq/llama-3.3-70b-versatile
  2. cerebras/qwen-3-235b-a22b-instruct-2507
  3. gemini/gemma-3-27b-it
  4. mistral/mistral-small-latest
  5. kr/claude-haiku-4.5
- Params : temperature=0, max_tokens=1500

## Exemple d’appel

```python
from backend.llm_router import call_naqil

# Appel généraliste
result = call_naqil("Dis bonjour.", "default")
print(result["status"], result.get("model"), result.get("content"))

# Appel traduction
result = call_naqil("Traduire ceci en arabe : ...", "translation_ar_fr")

# Appel parsing JSON
result = call_naqil("Parse ce texte en JSON : ...", "json_parsing")
```

## Règles absolues

- Jamais de "daif" par défaut.
- Jamais de génération de hadith.
- Si tous les modèles échouent : classification = "non-jugé".

## Providers utilisés

- groq
- kiro
- gemini
- cerebras
- mistral