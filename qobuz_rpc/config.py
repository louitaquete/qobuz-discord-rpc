"""Configuracao salva em %APPDATA%\\QobuzRPC\\config.json."""

import json
import os
import re
from pathlib import Path

APP_DIR_NAME = "QobuzRPC"

# Application ID do app "Qobuz" criado no Discord Developer Portal.
# O ID e publico (nao e segredo): pode ser embutido aqui para quem usar o instalador
# nao precisar configurar nada. Vazio = o app pergunta na primeira execucao.
DEFAULT_CLIENT_ID = ""

_CLIENT_ID_RE = re.compile(r"\d{17,20}")


def data_dir():
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _config_path():
    return data_dir() / "config.json"


def valid_client_id(value):
    return bool(_CLIENT_ID_RE.fullmatch((value or "").strip()))


def load():
    cfg = {
        "client_id": os.environ.get("QOBUZ_RPC_CLIENT_ID") or DEFAULT_CLIENT_ID,
        "enabled": True,
    }
    try:
        saved = json.loads(_config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    if isinstance(saved, dict):
        if saved.get("client_id"):
            cfg["client_id"] = str(saved["client_id"]).strip()
        if isinstance(saved.get("enabled"), bool):
            cfg["enabled"] = saved["enabled"]
    return cfg


def save(cfg):
    _config_path().write_text(json.dumps(cfg, indent=2), encoding="utf-8")
