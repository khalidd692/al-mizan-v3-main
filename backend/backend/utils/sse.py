"""Helpers pour Server-Sent Events conformes au protocole W3C."""

import json

def emit(event: str, data: dict) -> str:
    """Formate un événement SSE."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"

def keepalive() -> str:
    """Commentaire SSE pour maintenir la connexion."""
    return ": keepalive\n\n"