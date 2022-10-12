from lsp.server import server  # type: ignore

if __name__ == "__main__":
    print("Starting CLI Tools LSP server on STDIO...")
    server.start_io()
