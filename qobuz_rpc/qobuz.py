"""Leitura da musica atual a partir do titulo da janela do Qobuz."""

import re

from . import windows

# Titulo da janela: "Musica (feat. X) – Artista". Separa no ULTIMO traco com espacos,
# porque nomes de musica podem conter " - " (ex.: "Song - Remastered 2011").
SEPARATOR = re.compile(r"\s+[–—-]\s+")


def parse(title):
    """'Musica – Artista' -> (musica, artista); None se nao for uma musica."""
    title = title.strip()
    matches = list(SEPARATOR.finditer(title))
    if not matches:
        return None
    last = matches[-1]
    song = title[: last.start()].strip()
    artist = title[last.end():].strip()
    return (song, artist) if song and artist else None


def read():
    """Retorna (qobuz_aberto, faixa). faixa e (musica, artista) ou None."""
    titles = windows.qobuz_titles()
    for title in titles:
        track = parse(title)
        if track:
            return True, track
    return bool(titles), None
