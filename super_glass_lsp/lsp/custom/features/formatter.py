from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    Position,
    Range,
)

from pygls.lsp.types import (
    TextEdit,
)

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from super_glass_lsp.lsp.custom.features._feature import Feature
from super_glass_lsp.lsp.custom.features._debounce import Debounce

SuperGlassFormatResult = Optional[List[TextEdit]]


class Formatter(Feature):
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
        result = await self.shell()
        new_text = result.stdout.strip()
        # TODO: update the document with the new text so that each tool
        # incrementaly applies its changes on top of the previous
        edit = self.new_text_to_textedit(new_text)
        return edit

    def new_text_to_textedit(self, new_text: str) -> SuperGlassFormatResult:
        current_document = self.server.get_document_from_uri(self.text_doc_uri)
        end_line = len(current_document.lines)
        # NB:
        # `end_char` may need to use something like pygls.workspace.utf16_num_units(lines[-1])
        # in order to handle wide characters. I have seen some weirdness like a single char
        # being copied on every save. But it's hard to know what's going on behind the scenes.
        end_char = 0
        return [
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=end_line, character=end_char),
                ),
                new_text=new_text,
            )
        ]
