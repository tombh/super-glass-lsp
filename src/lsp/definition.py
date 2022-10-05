import logging
import subprocess
import typing
from typing import Any, Dict, List, Optional

from parse import parse  # type: ignore
from pygls.lsp.methods import (INITIALIZE, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_OPEN)
from pygls.lsp.types import (Diagnostic, DidChangeTextDocumentParams,
                             DidOpenTextDocumentParams, InitializeParams,
                             Position, Range)
from pygls.server import LanguageServer

from .clitool_config import InitializationOptions


class CLIToolsLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()

        self.user_config: Optional[InitializationOptions] = None
        """The user's configuration."""

    def initialize(self, params: InitializeParams):
        self.user_config = InitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )

    @property
    def configuration(self) -> Dict[str, Any]:
        """Return the server's actual configuration."""
        if not self.user_config:
            return {}

        # TODO: research if there is an equivalent .dataclass() converter
        return self.user_config.dict()


server = CLIToolsLanguageServer()


@server.feature(INITIALIZE)
def on_initialize(params: InitializeParams):
    server.initialize(params)


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


def parse_line(
    error_format: str, line_offset: int, col_offset: int, line: str
) -> Diagnostic:
    parsed = parse(error_format, line)
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
        line_number = parsed["line"]
        col_number = parsed["col"]
        message = parsed["msg"]

        line_number += line_offset
        col_number += col_offset

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line_number, character=col_number),
                end=Position(line=line_number, character=col_number),
            ),
            message=message,
            source=type(server).__name__,
        )
    return diagnostic


def diagnose(uri: str):
    document = server.workspace.get_document(uri)

    # TODO: onlty run the CLI tools that match the current language ID
    config = server.configuration["clitool_configs"][0]

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
        # Clear diagnostics
        server.publish_diagnostics(document.uri, diagnostics)
        return

    logging.error(msg=config["parsing"]["format"])

    for line in output.splitlines():
        diagnostic = parse_line(
            config["parsing"]["format"],
            config["parsing"]["line_offset"],
            config["parsing"]["col_offset"],
            line,
        )
        diagnostics.append(diagnostic)

    server.publish_diagnostics(document.uri, diagnostics)
