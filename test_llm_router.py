from backend.llm_router import call_naqil

result = call_naqil('Explique brièvement le concept de "isnad" dans les hadiths en 3 phrases maximum.', 'default')
print('Statut:', result.get('status'))
print('Modèle:', result.get('model'))
print('Réponse:', result.get('content', 'N/A'))