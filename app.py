"""
app.py
------
Servidor web do painel de controle de backups.

Roda o coletor de dados em segundo plano (a cada X minutos, configurável
no .env) e expõe o painel em http://0.0.0.0:5000 — acessível por qualquer
computador na mesma rede local através do IP desta máquina.

Como rodar:
    python app.py
"""

import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from fetch_data import fetch_and_store, get_db, init_db, DB_PATH

load_dotenv()

app = Flask(__name__)

FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))
STALE_HOURS = int(os.getenv("STALE_HOURS", "26"))  # considera "atrasado" se passou disso sem sucesso


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/data")
def api_data():
    if not os.path.exists(DB_PATH):
        init_db()

    conn = get_db()
    rows = conn.execute("SELECT * FROM backupsets ORDER BY client_name, backup_set_name").fetchall()
    last_fetch = conn.execute(
        "SELECT * FROM fetch_log ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    items = [dict(r) for r in rows]

    now = datetime.now(timezone.utc)
    for item in items:
        item["is_stale"] = _is_stale(item.get("last_success_backup_job_date"), now)

    summary = {
        "total": len(items),
        "success": sum(1 for i in items if i["status"] == "success" and not i["is_stale"]),
        "warning": sum(1 for i in items if i["status"] == "warning"),
        "error": sum(1 for i in items if i["status"] == "error"),
        "nomon": sum(1 for i in items if i["status"] == "nomon"),
        "stale": sum(1 for i in items if i["is_stale"]),
    }
    return jsonify({
        "items": items,
        "summary": summary,
        "last_fetch": dict(last_fetch) if last_fetch else None,
    })


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    ok, msg = fetch_and_store()
    return jsonify({"success": ok, "message": msg})


def _is_stale(last_success_str, now):
    if not last_success_str:
        return True
    try:
        last_success = _parse_dt(last_success_str)
    except (ValueError, TypeError):
        return False
    hours = (now - last_success).total_seconds() / 3600
    return hours > STALE_HOURS


def _parse_dt(value):
    # Tenta formatos comuns de data/hora que a API pode retornar.
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_store, "interval", minutes=FETCH_INTERVAL_MINUTES, next_run_time=datetime.now())
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    init_db()
    start_scheduler()
    print(f"Coletando dados a cada {FETCH_INTERVAL_MINUTES} minutos.")
    print("Painel disponível em http://0.0.0.0:5000  (acesse pelo IP desta máquina na rede)")
    app.run(host="0.0.0.0", port=5000, debug=False)
