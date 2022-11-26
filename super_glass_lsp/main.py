import logging

from super_glass_lsp.lsp.setup import server  # type: ignore

LSP_SERVER_NAME = "Super Glass Generic"


def main() -> None:
    from argparse import ArgumentParser
    from super_glass_lsp import __version__

    parser = ArgumentParser(description=f"{LSP_SERVER_NAME} Language Server")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--logfile", help="Path to log file")
    parser = server.custom.add_cli_args(parser)
    args = parser.parse_args()
    server.cli_args = args

    if args.logfile is not None:
        logging.basicConfig(
            filename=args.logfile,
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(level=logging.INFO)

    print(f"{LSP_SERVER_NAME} LSP server on STDIO...")
    server.start_io()  # type: ignore


if __name__ == "__main__":
    main()
