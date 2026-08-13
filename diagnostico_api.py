"""
diagnostico_api.py
-------------------
Testa os formatos mais comuns de autenticação contra a API do MSP Clouds
para descobrir qual é o esperado. Rode uma vez só, cole o resultado
completo de volta na conversa.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("MSPCLOUDS_API_KEY", "")
URL = "https://mspclouds.com/api/v1/cloudbackup/reports/summary"

if not KEY:
    print("MSPCLOUDS_API_KEY não está definida no .env — configure antes de rodar.")
    raise SystemExit(1)

tentativas = [
    ("Header Authorization: Bearer <key>", {"Authorization": f"Bearer {KEY}"}, {}),
    ("Header Authorization: <key> (sem Bearer)", {"Authorization": KEY}, {}),
    ("Header Api-Key", {"Api-Key": KEY}, {}),
    ("Header X-Api-Key", {"X-Api-Key": KEY}, {}),
    ("Header apikey", {"apikey": KEY}, {}),
    ("Header token", {"token": KEY}, {}),
    ("Query param api_key", {}, {"api_key": KEY}),
    ("Query param apikey", {}, {"apikey": KEY}),
    ("Query param key", {}, {"key": KEY}),
    ("Query param token", {}, {"token": KEY}),
    ("Basic Auth (usuário=key, senha vazia)", {}, {}),  # tratado à parte
]

print(f"Testando {len(tentativas)} formatos contra:\n{URL}\n")
print("=" * 70)

for nome, headers, params in tentativas:
    try:
        if nome.startswith("Basic Auth"):
            resp = requests.get(URL, auth=(KEY, ""), timeout=15)
        else:
            resp = requests.get(URL, headers=headers, params=params, timeout=15)
        status = resp.status_code
        corpo = resp.text[:200]
        marcador = "✅ PROVÁVEL SUCESSO" if status == 200 else ("⚠️ " if status != 400 else "  ")
        print(f"{marcador} [{status}] {nome}")
        if status != 400:
            print(f"      corpo: {corpo}")
    except requests.exceptions.RequestException as e:
        print(f"  [ERRO DE CONEXÃO] {nome} -> {e}")

print("=" * 70)
print("\nCopie e cole TODO o resultado acima de volta na conversa.")
