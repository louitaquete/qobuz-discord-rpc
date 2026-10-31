"""App de bandeja (icone ao lado do relogio) com menu de configuracao."""

import logging
import os
import re
import threading
import webbrowser

import pystray

from . import __version__, config, windows
from .icon import make_image
from .worker import Worker

log = logging.getLogger(__name__)

TITLE = "Qobuz Rich Presence"
PORTAL_URL = "https://discord.com/developers/applications"

CLIENT_ID_PROMPT = (
    "Cole o Application ID do Discord.\n\n"
    "Como obter: acesse discord.com/developers/applications, crie um app chamado "
    "\"Qobuz\" (esse nome aparece como \"Ouvindo Qobuz\") e copie o Application ID "
    "da página General Information."
)


class TrayApp:
    def __init__(self):
        self.cfg = config.load()
        self.status = "Iniciando…"
        self._dialog_open = threading.Lock()
        self.worker = Worker(self.cfg["client_id"], self.cfg["enabled"], self._on_status)
        self.icon = pystray.Icon("QobuzRPC", make_image(64), TITLE, menu=self._build_menu())

    # ---- menu ----------------------------------------------------------------
    def _build_menu(self):
        item = pystray.MenuItem
        return pystray.Menu(
            item(lambda _: self.status, None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("Mostrar no Discord", self._toggle_enabled, checked=lambda _: self.cfg["enabled"]),
            item("Iniciar com o Windows", self._toggle_autostart, checked=lambda _: windows.is_autostart()),
            pystray.Menu.SEPARATOR,
            item("Configurar Application ID…", self._configure_client_id),
            item("Como obter o Application ID", lambda *_: webbrowser.open(PORTAL_URL)),
            item("Abrir pasta de logs", lambda *_: os.startfile(config.data_dir())),
            pystray.Menu.SEPARATOR,
            item(f"Sobre (v{__version__})", lambda *_: self.icon.notify(
                "Rich Presence do Qobuz para o Discord.\ngithub.com/louitaquete/qobuz-discord-rpc", TITLE)),
            item("Sair", self._quit),
            # clique esquerdo no icone: mostra o status atual
            item("status", lambda *_: self.icon.notify(self.status, TITLE), default=True, visible=False),
        )

    # ---- acoes ---------------------------------------------------------------
    def _on_status(self, text):
        if text == self.status:
            return
        self.status = text
        try:
            self.icon.title = f"{TITLE}\n{text}"[:127]
            self.icon.update_menu()
        except Exception:
            pass

    def _toggle_enabled(self, *_):
        self.cfg["enabled"] = not self.cfg["enabled"]
        config.save(self.cfg)
        self.worker.set_enabled(self.cfg["enabled"])
        self.icon.update_menu()

    def _toggle_autostart(self, *_):
        try:
            windows.set_autostart(not windows.is_autostart())
        except OSError:
            log.exception("nao foi possivel alterar o inicio com o Windows")
        self.icon.update_menu()

    def _configure_client_id(self, *_):
        threading.Thread(target=self._ask_client_id, daemon=True).start()

    def _ask_client_id(self):
        if not self._dialog_open.acquire(blocking=False):
            return  # ja existe uma janela aberta
        try:
            import tkinter as tk
            from tkinter import messagebox, simpledialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                value = self.cfg["client_id"]
                while True:
                    value = simpledialog.askstring(TITLE, CLIENT_ID_PROMPT, initialvalue=value, parent=root)
                    if value is None:
                        return
                    value = value.strip()
                    if config.valid_client_id(value):
                        break
                    messagebox.showwarning(TITLE, "O Application ID deve ter só números (17 a 20 dígitos).", parent=root)
                self.cfg["client_id"] = value
                config.save(self.cfg)
                self.worker.set_client_id(value)
            finally:
                root.destroy()
        finally:
            self._dialog_open.release()

    def _quit(self, *_):
        self.worker.stop()
        self.worker.join(timeout=3)
        self.icon.stop()

    # ---- ciclo de vida -------------------------------------------------------
    def _setup(self, icon):
        icon.visible = True
        self.worker.start()
        if not self.cfg["client_id"]:
            self._configure_client_id()  # primeira execucao

    def run(self):
        self.icon.run(setup=self._setup)
