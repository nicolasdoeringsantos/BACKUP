"""
fetch_data.py
--------------
Busca o relatório de status de backup na API do MSP Clouds
(GET /api/v1/cloudbackup/reports/summary) e salva os dados
no banco local (data/backups.db) para o painel exibir.

Pode ser executado manualmente:
    python fetch_data.py

Ou é chamado automaticamente em segundo plano pelo app.py
(agendador embutido, não precisa configurar Task Scheduler).
"""

import os
import sqlite3
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://mspclouds.com/api/v1/cloudbackup/reports/summary"
API_KEY = os.getenv("MSPCLOUDS_API_KEY", "")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "backups.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backupsets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            client_name TEXT,
            login_name TEXT,
            login_description TEXT,
            backup_set_id TEXT,
            backup_set_name TEXT,
            backup_set_type TEXT,
            destination_name TEXT,
            status TEXT,
            last_backup_job_date TEXT,
            last_backup_job_status_description TEXT,
            last_backup_job_url TEXT,
            last_success_backup_job_date TEXT,
            fetched_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TEXT,
            success INTEGER,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()


def _request_headers():
    return {
        "Accept": "application/json",
    }


def _request_params():
    # A API do MSP Clouds espera a chave como parâmetro de URL (?api_key=...)
    return {
        "api_key": API_KEY,
    }


def fetch_and_store():
    """Busca os dados na API e substitui o snapshot atual no banco local."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()

    if not API_KEY:
        _log_fetch(now, False, "MSPCLOUDS_API_KEY não configurada no .env")
        return False, "Chave da API não configurada (veja o arquivo .env)"

    try:
        resp = requests.get(API_URL, headers=_request_headers(), params=_request_params(), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except requests.exceptions.RequestException as e:
        _log_fetch(now, False, str(e))
        return False, f"Erro ao chamar a API: {e}"

    rows = []
    clients = payload.get("clients", [])
    for client in clients:
        client_id = client.get("id")
        client_name = client.get("name")
        for bs in client.get("backupsets", []):
            rows.append((
                client_id,
                client_name,
                bs.get("login_name"),
                bs.get("login_description"),
                bs.get("backup_set_id"),
                bs.get("backup_set_name"),
                bs.get("backup_set_type"),
                bs.get("destination_name"),
                bs.get("status"),
                bs.get("last_backup_job_date"),
                bs.get("last_backup_job_status_description"),
                bs.get("last_backup_job_url"),
                bs.get("last_success_backup_job_date"),
                now,
            ))

    conn = get_db()
    conn.execute("DELETE FROM backupsets")
    conn.executemany("""
        INSERT INTO backupsets (
            client_id, client_name, login_name, login_description,
            backup_set_id, backup_set_name, backup_set_type, destination_name,
            status, last_backup_job_date, last_backup_job_status_description,
            last_backup_job_url, last_success_backup_job_date, fetched_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()

    _log_fetch(now, True, f"{len(rows)} tarefas de backup atualizadas")
    return True, f"{len(rows)} tarefas atualizadas com sucesso"


def _log_fetch(ts, success, message):
    conn = get_db()
    conn.execute(
        "INSERT INTO fetch_log (fetched_at, success, message) VALUES (?, ?, ?)",
        (ts, 1 if success else 0, message)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    ok, msg = fetch_and_store()
    print(("[OK] " if ok else "[ERRO] ") + msg)
