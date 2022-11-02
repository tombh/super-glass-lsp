from typing import List, Optional, TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    Position,
)

from pygls.lsp import (
    CompletionItem,
    CompletionList,
)

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from super_glass_lsp.lsp.custom.features import Feature, Debounced


class Completer(Feature):
    def __init__(self, server: "CustomLanguageServer"):
        super().__init__(server)

    async def run(
        self, uri: str, cursor_position: Position
    ) -> Optional[CompletionList]:
        if self.server.configuration is None:
            self.server.logger.warning(
                "Received completion request without any server config"
            )
            return None

        language_id = self.server.workspace.get_document(uri).language_id

        configs = self.server.custom.get_all_config_by(
            LSPFeature.completion, language_id
        )
        completions = []
        for id, config in configs.items():
            self.config_id = id
            self.server.logger.debug(f"Running completion request for: {id}: {config}")
            self.config = config
            items = await self.complete(uri, cursor_position)
            completions.extend(items)

        return CompletionList(
            is_incomplete=True,
            items=completions,
        )

    async def complete(
        self, text_doc_uri: str, cursor_position: Position
    ) -> List[CompletionItem]:
        if self.config is None:
            return []

        word = self.get_word_under_cursor(text_doc_uri, cursor_position)

        output = await self.run_cli_tool(
            self.config.command, text_doc_uri, word, cursor_position
        )

        if isinstance(output, Debounced):
            return self.get_cache(text_doc_uri)

        items = []
        for line in output.splitlines():
            item = CompletionItem(label=line)
            items.append(item)
        self.set_cache(text_doc_uri, items)

        return items

    async def run_cli_tool(
        self,
        command: str,
        text_doc_uri: str,
        word: str,
        cursor_position: Position,
    ) -> Union[str, Debounced]:
        # TODO: probably refactor into a list of Tuple pairs?
        command = command.replace("{word}", word)
        command = command.replace("{cursor_line}", str(cursor_position.line))
        command = command.replace("{cursor_char}", str(cursor_position.character))

        result = await self.shell(command, text_doc_uri)
        if isinstance(result, Debounced):
            return result

        return result.stdout.strip()

    def get_word_under_cursor(self, uri: str, cursor_position: Position):
        doc = self.server.workspace.get_document(uri)
        word = doc.word_at_position(cursor_position)
        return word
