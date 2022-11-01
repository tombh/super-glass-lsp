from typing import List, Optional, Union

from pygls.lsp.types import (
    Position,
    Range,
)

from pygls.lsp.types import (
    TextEdit,
)

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from super_glass_lsp.lsp.custom.features import Feature, Debounced

SuperGlassFormatResult = Optional[List[TextEdit]]


class Formatter(Feature):
    def run(self, text_doc_uri: str) -> SuperGlassFormatResult:
        document = self.get_document_from_uri(text_doc_uri)
        configs = self.server.custom.get_all_config_by(
            LSPFeature.formatter, document.language_id
        )

        edit: SuperGlassFormatResult = None
        for id, config in configs.items():
            self.config_id = id
            self.config = config
            if document.language_id == config.language_id:
                new_text = self.run_cli_tool(config.command, text_doc_uri)
                if not isinstance(new_text, Debounced) and new_text != "":
                    edit = self.new_text_to_textedit(new_text)
        return edit

    def new_text_to_textedit(self, new_text: str) -> SuperGlassFormatResult:
        lines = new_text.splitlines()
        end_line = len(lines)
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

    def run_cli_tool(
        self,
        command: str,
        text_doc_uri: str,
    ) -> Union[str, Debounced]:
        result = self.shell(command, text_doc_uri)
        if isinstance(result, Debounced):
            return result
        return result.stdout.strip()
