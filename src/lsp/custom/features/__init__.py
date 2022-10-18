from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer


class Feature:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        # TODO: Use the config ID of the currently active feature?
        self.name = type(server).__name__
