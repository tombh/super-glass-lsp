import logging

from src.lsp.setup import server  # type: ignore


def main() -> None:
    from argparse import ArgumentParser

    from src import __version__

    parser = ArgumentParser(description="CLI Tools Language Server")

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--logfile")
    args = parser.parse_args()

    if args.logfile is not None:
        logging.basicConfig(
            filename=args.logfile,
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(level=logging.INFO)

    logging.getLogger("pygls").setLevel(logging.WARNING)

    print("Starting CLI Tools LSP server on STDIO...")
    server.start_io()  # type: ignore


if __name__ == "__main__":
    main()
