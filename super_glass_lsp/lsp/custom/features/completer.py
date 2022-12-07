from typing import List, Optional, TYPE_CHECKING

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
from ._feature import Feature
from ._commands import Commands
from ._debounce import Debounce


class Completer(Feature, Commands):
    @classmethod
    async def run_all(
        cls,
        server: "CustomLanguageServer",
        text_doc_uri: str,
        cursor_position: Position,
    ) -> Optional[CompletionList]:
        language_id = server.get_document_from_uri(text_doc_uri).language_id
        configs = server.custom.get_all_config_by(LSPFeature.completion, language_id)
        completions = []
        for id, config in configs.items():
            completer = cls(server, id, text_doc_uri)
            server.logger.debug(f"Running completion request for: {id}: {config}")
            if server.debounces[completer.cache_key()].is_debounced():
                items = completer.get_cache()
            else:
                items = await completer.complete(cursor_position)
                completer.set_cache(items)
            completions.extend(items)

        return CompletionList(
            is_incomplete=True,
            items=completions,
        )

    def __init__(
        self, server: "CustomLanguageServer", config_id: str, text_doc_uri: str
    ):
        super().__init__(server, config_id, text_doc_uri)

        Debounce.init(
            self.server,
            config_id,
            self.cache_key(),
        )

    async def complete(self, cursor_position: Position) -> List[CompletionItem]:
        word = self.get_wordish_under_cursor(cursor_position)

        output = await self.run_cli_tool(word, cursor_position)

        items = []
        for line in output.splitlines():
            item = CompletionItem(label=line)
            items.append(item)

        return items

    async def run_cli_tool(
        self,
        word: str,
        cursor_position: Position,
    ) -> str:
        if isinstance(self.command, list):
            raise Exception("Completions do not support multiple commands")

        replacements = [
            ("{word}", word),
            ("{cursor_line}", str(cursor_position.line)),
            ("{cursor_char}", str(cursor_position.character)),
        ]
        command = self.resolve_commands(replacements)
        if isinstance(command, list):
            raise Exception

        result = await self.shell(command)
        return result.stdout
