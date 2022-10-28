import logging

from super_glass_lsp.lsp.setup import server  # type: ignore


def main() -> None:
    from argparse import ArgumentParser

    from super_glass_lsp import __version__

    parser = ArgumentParser(description="Super Glass Generic Language Server")

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

    print("Starting Super Glass LSP server on STDIO...")
    server.start_io()  # type: ignore


if __name__ == "__main__":
    main()
