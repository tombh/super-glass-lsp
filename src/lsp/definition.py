import logging
import subprocess
from typing import List

# type: ignore
from parse import parse
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE, TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.types import (Diagnostic, DidChangeTextDocumentParams,
                             DidOpenTextDocumentParams, Position, Range)
from pygls.server import LanguageServer


class CLIToolsLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()


server = CLIToolsLanguageServer()

config = {
    "command": ["jq", "."],
    "efm": "{msg} at line {line:d}, column {col:d}",
    "language_id": "json",
}


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(params: DidChangeTextDocumentParams):
    diagnose(
        params.text_document.uri,
    )


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(params: DidOpenTextDocumentParams):
    diagnose(
        params.text_document.uri,
    )


def diagnose(uri: str):
    document = server.workspace.get_document(uri)

    if document.language_id != config["language_id"]:
        return

    result = subprocess.run(
        config["command"],
        input=document.source,
        text=True,
        capture_output=True,
        check=False,
    )
    output = result.stderr.strip()

    diagnostics: List[Diagnostic] = []

    if not output:
        server.publish_diagnostics(document.uri, diagnostics)
        return

    parsed = parse(config["efm"], output)
    if parsed is None:
        # TODO: What's the proper way of communicating this?
        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=1),
            ),
            message="CLI Tool LSP failed to parse CLI output",
            source=type(server).__name__,
        )
    else:
        line = parsed["line"]
        col = parsed["col"]
        message = parsed["msg"]

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col),
            ),
            message=message,
            source=type(server).__name__,
        )
    diagnostics.append(diagnostic)

    server.publish_diagnostics(document.uri, diagnostics)
