from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE, TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import (Diagnostic, DidChangeTextDocumentParams,
                             DidOpenTextDocumentParams, Position, Range)
from pygls.server import LanguageServer


class CLIToolsLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()


server = CLIToolsLanguageServer()


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(params: DidChangeTextDocumentParams):
    diagnose(document_uri=params.text_document.uri)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(params: DidOpenTextDocumentParams):
    diagnose(document_uri=params.text_document.uri)


def diagnose(document_uri: str):
    line = 0
    col = 0
    message = "Hello LSP World!"

    text_doc = server.workspace.get_document(document_uri)

    diagnostic = Diagnostic(
        range=Range(
            start=Position(line=line, character=col),
            end=Position(line=line, character=col + 2),
        ),
        message=message,
        source=type(server).__name__,
    )
    server.publish_diagnostics(text_doc.uri, [diagnostic])
