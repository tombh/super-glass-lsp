import logging

from src.lsp.setup import server  # type: ignore


def main() -> None:
    from argparse import ArgumentParser

    from src import __version__

    parser = ArgumentParser(description="CLI Tools Language Server")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("pygls").setLevel(logging.WARNING)
    print("Starting CLI Tools LSP server on STDIO...")
    server.start_io()  # type: ignore


if __name__ == "__main__":
    main()
