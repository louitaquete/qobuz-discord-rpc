"""Discord Rich Presence para o Qobuz (app desktop, Windows).

Le a musica atual pelo titulo da janela do Qobuz e envia ao Discord.

Uso:
    pip install pypresence
    python qobuz_rpc.py --list     # mostra o titulo lido e como foi interpretado
    python qobuz_rpc.py            # roda o Rich Presence

Antes: crie um app em https://discord.com/developers/applications, copie o
"Application ID" e cole em CLIENT_ID (ou defina a variavel QOBUZ_RPC_CLIENT_ID).
O nome do app vira o texto "Ouvindo ..." no perfil, entao chame ele de "Qobuz".
"""

import ctypes
import os
import re
import sys
import time
from ctypes import wintypes

import json
import urllib.parse
import urllib.request

from pypresence import ActivityType, Presence, StatusDisplayType

CLIENT_ID = os.environ.get("QOBUZ_RPC_CLIENT_ID", "COLE_O_APPLICATION_ID_AQUI")
EXE_NAME = "qobuz.exe"
POLL_SECONDS = 3
MIN_UPDATE_SECONDS = 15      # o Discord limita atualizacoes de presence
LARGE_IMAGE = "qobuz"        # nome de um asset enviado em Rich Presence > Art Assets

# Titulo da janela: "Musica (feat. X) – Artista". Separa no ULTIMO traco com espacos.
SEPARATOR = re.compile(r"\s+[–—-]\s+")

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def exe_name(hwnd):
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def qobuz_titles():
    """Titulos das janelas visiveis do Qobuz."""
    titles = []

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length and exe_name(hwnd) == EXE_NAME:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return titles


def parse(title):
    """'Musica – Artista' -> (musica, artista); None se nao for uma musica."""
    parts = SEPARATOR.split(title.strip())
    if len(parts) < 2:
        return None
    # divide so no ultimo separador: nomes de musica podem ter " - " (ex.: "Remastered")
    m = list(SEPARATOR.finditer(title.strip()))[-1]
    song = title.strip()[: m.start()].strip()
    artist = title.strip()[m.end():].strip()
    return (song, artist) if song and artist else None


def current_track():
    for title in qobuz_titles():
        track = parse(title)
        if track:
            return track
    return None


_cover_cache = {}


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "qobuz-rpc/1.0"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def _artist_ok(found, wanted):
    found, wanted = found.lower(), wanted.lower()
    return found in wanted or wanted in found


def _from_deezer(clean, artist):
    for q in (f'track:"{clean}" artist:"{artist}"', f"{artist} {clean}"):
        data = _get_json(f"https://api.deezer.com/search?q={urllib.parse.quote(q)}&limit=5").get("data") or []
        for item in data:
            if _artist_ok(item["artist"]["name"], artist):
                return item["album"].get("cover_xl") or item["album"].get("cover_big")
    return None


def _from_itunes(clean, artist):
    q = urllib.parse.quote(f"{artist} {clean}")
    data = _get_json(f"https://itunes.apple.com/search?term={q}&entity=song&limit=5").get("results") or []
    for item in data:
        if _artist_ok(item.get("artistName", ""), artist) and item.get("artworkUrl100"):
            return item["artworkUrl100"].replace("100x100bb", "600x600bb")
    return None


def cover_url(song, artist):
    """Busca a capa do album (Deezer, depois iTunes). Retorna None se nao achar."""
    key = (song, artist)
    if key in _cover_cache:
        return _cover_cache[key]
    clean = re.sub(r"\s*[\(\[].*?[\)\]]", "", song).strip() or song  # tira "(feat. ...)"
    url = None
    for name, fn in (("Deezer", _from_deezer), ("iTunes", _from_itunes)):
        try:
            url = fn(clean, artist)
        except Exception as e:
            print(f"[capa] {name} falhou: {e!r}")
            continue
        print(f"[capa] {name}: {url or 'nada encontrado'}")
        if url:
            break
    _cover_cache[key] = url
    return url


def connect():
    while True:
        try:
            rpc = Presence(CLIENT_ID)
            rpc.connect()
            print("Conectado ao Discord.")
            return rpc
        except Exception:
            print("Discord nao encontrado, tentando de novo em 10s...")
            time.sleep(10)


def main():
    if "--list" in sys.argv:
        titles = qobuz_titles()
        if not titles:
            print("Nenhuma janela visivel do Qobuz. O app esta aberto?")
        for t in titles:
            print(f"titulo={t!r} -> interpretado={parse(t)}")
        return

    if "--cover" in sys.argv:
        i = sys.argv.index("--cover")
        song, artist = sys.argv[i + 1], sys.argv[i + 2]
        print("resultado:", cover_url(song, artist))
        return

    if CLIENT_ID.startswith("COLE"):
        sys.exit("Defina o CLIENT_ID (Application ID do Discord) no topo do arquivo.")

    rpc = connect()
    last, started, last_sent = None, 0.0, 0.0

    while True:
        track = current_track()
        if track != last:
            if track is not None:
                started = time.time()
            if time.time() - last_sent >= MIN_UPDATE_SECONDS:
                try:
                    if track is None:
                        rpc.clear()
                    else:
                        song, artist = track
                        rpc.update(
                            activity_type=ActivityType.LISTENING,
                            status_display_type=StatusDisplayType.DETAILS,
                            details=song[:128],
                            state=artist[:128],
                            large_image=cover_url(song, artist) or LARGE_IMAGE,
                            small_image=LARGE_IMAGE,
                            small_text="Qobuz",
                            start=int(started),
                        )
                    last, last_sent = track, time.time()
                except Exception:
                    print("Perdi a conexao com o Discord, reconectando...")
                    rpc = connect()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
