"""Thread que le o Qobuz e mantem o Rich Presence do Discord atualizado."""

import asyncio
import logging
import threading
import time

from pypresence import ActivityType, Presence, StatusDisplayType

from . import covers, qobuz

log = logging.getLogger(__name__)

POLL_SECONDS = 3
RECONNECT_SECONDS = 10
MIN_UPDATE_SECONDS = 15      # o Discord limita atualizacoes de presence
LOGO_ASSET = "qobuz"         # asset enviado em Rich Presence > Art Assets


class Worker(threading.Thread):
    def __init__(self, client_id, enabled, on_status):
        super().__init__(name="qobuz-rpc-worker", daemon=True)
        self._client_id = client_id
        self._enabled = enabled
        self._on_status = on_status
        self._quit = threading.Event()
        self._wake = threading.Event()
        self._reconnect = False
        self._lock = threading.Lock()

    # ---- controle (chamado pela bandeja) -------------------------------------
    def set_enabled(self, enabled):
        with self._lock:
            self._enabled = enabled
        self._wake.set()

    def set_client_id(self, client_id):
        with self._lock:
            self._client_id = client_id
            self._reconnect = True
        self._wake.set()

    def stop(self):
        self._quit.set()
        self._wake.set()

    # ---- internos ------------------------------------------------------------
    def _snapshot(self):
        with self._lock:
            reconnect, self._reconnect = self._reconnect, False
            return self._client_id, self._enabled, reconnect

    def _status(self, text):
        try:
            self._on_status(text)
        except Exception:
            log.exception("falha ao atualizar o status")

    def _sleep(self, seconds):
        self._wake.wait(seconds)
        self._wake.clear()

    @staticmethod
    def _close(rpc):
        try:
            rpc.clear()
        except Exception:
            pass
        try:
            rpc.close()
        except Exception:
            pass

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rpc, last, seen, started, last_sent = None, None, None, 0.0, 0.0

        while not self._quit.is_set():
            client_id, enabled, reconnect = self._snapshot()

            if rpc is not None and (reconnect or not enabled or not client_id):
                self._close(rpc)
                rpc, last = None, None

            if not client_id:
                self._status("Defina o Application ID do Discord")
                self._sleep(2)
                continue
            if not enabled:
                self._status("Pausado")
                self._sleep(2)
                continue

            if rpc is None:
                try:
                    rpc = Presence(client_id, loop=loop)
                    rpc.connect()
                    log.info("conectado ao Discord")
                    last = None
                except Exception as exc:
                    log.info("Discord nao encontrado: %r", exc)
                    rpc = None
                    self._status("Abra o Discord para conectar")
                    self._sleep(RECONNECT_SECONDS)
                    continue

            try:
                is_open, track = qobuz.read()
                if track != seen:
                    seen = track
                    started = time.time()
                if track != last:
                    if time.time() - last_sent >= MIN_UPDATE_SECONDS:
                        self._publish(rpc, track, started)
                        last, last_sent = track, time.time()
                if track:
                    self._status(f"Ouvindo: {track[0]} – {track[1]}")
                else:
                    self._status("Aguardando música do Qobuz" if is_open else "Qobuz não está aberto")
            except Exception as exc:
                log.warning("conexao com o Discord perdida: %r", exc)
                self._close(rpc)
                rpc = None
                self._status("Reconectando ao Discord…")
                self._sleep(RECONNECT_SECONDS)
                continue

            self._sleep(POLL_SECONDS)

        if rpc is not None:
            self._close(rpc)

    @staticmethod
    def _publish(rpc, track, started):
        if track is None:
            rpc.clear()
            return
        song, artist = track
        rpc.update(
            activity_type=ActivityType.LISTENING,
            status_display_type=StatusDisplayType.DETAILS,  # mostra a musica no status
            details=song[:128],
            state=artist[:128],
            large_image=covers.cover_url(song, artist) or LOGO_ASSET,
            small_image=LOGO_ASSET,
            small_text="Qobuz",
            start=int(started),
        )
