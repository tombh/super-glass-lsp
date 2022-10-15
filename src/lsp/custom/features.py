from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)

from pygls.lsp import (
    CompletionParams,
    CompletionList,
)

from .diagnoser import Diagnoser
from .completer import Completer


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

    @classmethod
    def completion_request(
        cls, ls: "CustomLanguageServer", params: CompletionParams
    ) -> Optional[CompletionList]:
        completer = Completer(ls)
        return completer.run(params.text_document.uri, params.position)
