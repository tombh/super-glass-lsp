from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    TextEdit,
)

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from ._feature import Feature
from ._debounce import Debounce
from ._commands import Commands

SuperGlassFormatResult = Optional[List[TextEdit]]


class Formatter(Feature, Commands):
    @classmethod
    async def run_all(
        cls, server: "CustomLanguageServer", text_doc_uri: str
    ) -> SuperGlassFormatResult:
        configs = Feature.get_configs(server, text_doc_uri, LSPFeature.formatter)

        edit: SuperGlassFormatResult = None
        for id, config in configs.items():
            formatter = cls(server, id, text_doc_uri)
            if not formatter.debouncer.is_debounced():
                edit = await formatter.run_one()
            else:
                server.show_message("Too many formatting requests")
        return edit

    def __init__(
        self, server: "CustomLanguageServer", config_id: str, text_doc_uri: str
    ):
        super().__init__(server, config_id, text_doc_uri)

        Debounce.init(
            self.server,
            config_id,
            self.cache_key(),
        )

    async def run_one(self) -> SuperGlassFormatResult:
        if isinstance(self.command, list):
            raise Exception("Formatters do not support multiple commands")

        result = await self.shell(self.command)
        new_text = result.stdout
        # TODO: update the document with the new text so that each tool
        # incrementaly applies its changes on top of the previous
        edit = self.new_text_to_textedit(new_text)
        return edit

    def new_text_to_textedit(self, new_text: str) -> SuperGlassFormatResult:
        return [
            TextEdit(
                range=self.range_for_whole_document(),
                new_text=new_text,
            )
        ]
