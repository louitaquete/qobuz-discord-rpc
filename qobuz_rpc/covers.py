"""Busca da capa do album (Deezer e, se falhar, iTunes). APIs publicas, sem chave."""

import json
import logging
import re
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)
_cache = {}


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "qobuz-discord-rpc/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)


def _artist_ok(found, wanted):
    found, wanted = found.lower(), wanted.lower()
    return found in wanted or wanted in found


def _from_deezer(song, artist):
    for q in (f'track:"{song}" artist:"{artist}"', f"{artist} {song}"):
        url = f"https://api.deezer.com/search?q={urllib.parse.quote(q)}&limit=5"
        for item in _get_json(url).get("data") or []:
            if _artist_ok(item["artist"]["name"], artist):
                return item["album"].get("cover_xl") or item["album"].get("cover_big")
    return None


def _from_itunes(song, artist):
    q = urllib.parse.quote(f"{artist} {song}")
    url = f"https://itunes.apple.com/search?term={q}&entity=song&limit=5"
    for item in _get_json(url).get("results") or []:
        if _artist_ok(item.get("artistName", ""), artist) and item.get("artworkUrl100"):
            return item["artworkUrl100"].replace("100x100bb", "600x600bb")
    return None


def cover_url(song, artist):
    """URL da capa ou None. Resultados ficam em cache durante a execucao."""
    key = (song, artist)
    if key in _cache:
        return _cache[key]
    clean = re.sub(r"\s*[\(\[].*?[\)\]]", "", song).strip() or song  # tira "(feat. ...)"
    url = None
    for name, fn in (("Deezer", _from_deezer), ("iTunes", _from_itunes)):
        try:
            url = fn(clean, artist)
        except Exception as exc:
            log.warning("capa: %s falhou: %r", name, exc)
            continue
        log.info("capa: %s -> %s", name, url or "nada encontrado")
        if url:
            break
    _cache[key] = url
    return url
