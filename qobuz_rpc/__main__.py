"""Ponto de entrada: abre o app de bandeja. Opcoes de diagnostico: --list e --cover."""

import argparse
import logging
import logging.handlers
import sys

from . import __version__, config


def _setup_logging(console):
    handlers = [logging.handlers.RotatingFileHandler(
        config.data_dir() / "qobuz-rpc.log", maxBytes=200_000, backupCount=1, encoding="utf-8")]
    if console and sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="qobuz-rpc", description="Rich Presence do Qobuz para o Discord")
    parser.add_argument("--list", action="store_true", help="mostra o titulo lido da janela do Qobuz")
    parser.add_argument("--cover", nargs=2, metavar=("MUSICA", "ARTISTA"), help="testa a busca de capa")
    parser.add_argument("--version", action="version", version=f"qobuz-rpc {__version__}")
    args = parser.parse_args(argv)

    _setup_logging(console=bool(args.list or args.cover))

    if args.list:
        from . import qobuz, windows
        titles = windows.qobuz_titles()
        if not titles:
            print("Nenhuma janela visivel do Qobuz. O app esta aberto?")
        for title in titles:
            print(f"titulo={title!r} -> interpretado={qobuz.parse(title)}")
        return

    if args.cover:
        from . import covers
        print("resultado:", covers.cover_url(*args.cover))
        return

    from . import windows
    try:  # texto nitido em telas de alta resolucao (janelas de configuracao)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    mutex = windows.acquire_single_instance()
    if mutex is None:
        windows.message_box("O Qobuz Rich Presence já está em execução. Procure o ícone na bandeja, perto do relógio.")
        return

    from .tray import TrayApp
    TrayApp().run()


if __name__ == "__main__":
    main()
