import typing
from typing import Dict, Optional

from pygls.lsp.methods import (
    INITIALIZE,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
)
from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
)
from pygls.server import LanguageServer

from .clitool_config import InitializationOptions
from .diagnoser import Diagnoser


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
    def configuration(self) -> Optional[InitializationOptions]:
        """Return the server's actual configuration."""
        return self.user_config


server = CLIToolsLanguageServer()


@server.feature(INITIALIZE)
def on_initialize(params: InitializeParams):
    server.initialize(params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: CLIToolsLanguageServer, params: DidChangeTextDocumentParams):
    diagnoser = Diagnoser(ls)
    diagnoser.run(params.text_document.uri)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: CLIToolsLanguageServer, params: DidOpenTextDocumentParams):
    diagnoser = Diagnoser(ls)
    diagnoser.run(params.text_document.uri)
