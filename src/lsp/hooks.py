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

from .custom.features import Features as CustomFeatures
from .server import CustomLanguageServer

server = CustomLanguageServer()


@server.feature(INITIALIZE)
def on_initialize(params: InitializeParams):
    server.initialize(params)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: CustomLanguageServer, params: DidChangeTextDocumentParams):
    CustomFeatures.did_change(ls, params)


@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: CustomLanguageServer, params: DidOpenTextDocumentParams):
    CustomFeatures.did_open(ls, params)
