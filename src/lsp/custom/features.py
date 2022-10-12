from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)

from .diagnoser import Diagnoser


class Features:
    @classmethod
    def did_change(
        cls, ls: "CustomLanguageServer", params: DidChangeTextDocumentParams
    ):
        diagnoser = Diagnoser(ls)
        diagnoser.run(params.text_document.uri)

    @classmethod
    def did_open(cls, ls: "CustomLanguageServer", params: DidOpenTextDocumentParams):
        diagnoser = Diagnoser(ls)
        diagnoser.run(params.text_document.uri)
