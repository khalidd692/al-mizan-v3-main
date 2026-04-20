import requests, hashlib, json, time, os, logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path

OMNIROUTE_URL = "http://localhost:20128/v1/chat/completions"
AUDIT_LOG = Path("logs/mizan_audit.jsonl")
AUDIT_LOG.parent.mkdir(exist_ok=True)

COMBOS = {
    "default": "almizann",
    "translation_ar_fr": "almizann-traduction",
    "json_parsing": "almizann-json",
}

CACHE_TTL = {
    "translation_ar_fr": 30 * 86400,
    "json_parsing": 7 * 86400,
    "default": 0,
}

_cache = {}  # {hash: (timestamp, result)}

def call_naqil(prompt: str, task_type: str = "default", system: str = None) -> dict:
    """
    Appelle OmniRoute via le combo adapté à la tâche.

    Règle Naqil ABSOLUE :
    - Si tous les modèles échouent → retour "non-jugé"
    - JAMAIS "daif" par défaut
    - Les LLMs ne jugent pas, ils formatent seulement
    """
    combo = COMBOS.get(task_type, COMBOS["default"])
    prompt_hash = hashlib.sha256(f"{prompt}{task_type}".encode()).hexdigest()[:16]

    # Cache check
    ttl = CACHE_TTL.get(task_type, 0)
    if ttl > 0 and prompt_hash in _cache:
        ts, cached = _cache[prompt_hash]
        if time.time() - ts < ttl:
            return cached

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.time()
    model_used = None
    status = "ok"
    error_msg = None

    try:
        r = requests.post(
            OMNIROUTE_URL,
            json={
                "model": f"combo:{combo}",
                "messages": messages,
                "max_tokens": 2000 if task_type == "default"
                              else (3000 if task_type == "translation_ar_fr"
                              else 1500),
                "temperature": 0.2 if task_type == "default"
                               else (0.1 if task_type == "translation_ar_fr"
                               else 0),
            },
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        model_used = data.get("model", "unknown")
        result = {
            "status": "ok",
            "content": content,
            "model": model_used,
            "confidence_degraded": False,
        }
    except Exception as e:
        status = "unavailable"
        error_msg = str(e)[:200]
        result = {
            "status": "unavailable",
            "classification": "non-jugé",  # JAMAIS "daif"
            "confidence_degraded": True,
            "content": None,
            "error": error_msg,
        }

    latency_ms = int((time.time() - start) * 1000)

    # Audit log
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "task_type": task_type,
        "combo": combo,
        "model_used": model_used,
        "prompt_hash": prompt_hash,
        "latency_ms": latency_ms,
        "status": status,
        "error": error_msg,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Cache store
    if ttl > 0 and status == "ok":
        _cache[prompt_hash] = (time.time(), result)

    return result


def call_fast(prompt, system=None) -> dict:
    """
    Appelle le combo 'almizann-fast' pour une réponse rapide.
    Retour : {"status": "ok"|"unavailable", "content": str, "model": str}
    """
    return call_naqil(prompt, task_type="almizann-fast", system=system)

def call_translation(prompt, system=None) -> dict:
    """
    Appelle le combo 'almizann-traduction' pour la traduction.
    Cache mémoire 30 jours sur hash(prompt).
    Retour : {"status": "ok"|"unavailable", "content": str, "model": str}
    """
    return call_naqil(prompt, task_type="almizann-traduction", system=system)

def call_json(prompt, system=None) -> dict:
    """
    Appelle le combo 'almizann-json' pour parsing JSON.
    Retour : {"status": "ok"|"unavailable", "content": str, "model": str}
    """
    return call_naqil(prompt, task_type="almizann-json", system=system)

if __name__ == "__main__":
    # Auto-test minimal
    print("Test default:", call_naqil("Dis bonjour en français.", "default"))
