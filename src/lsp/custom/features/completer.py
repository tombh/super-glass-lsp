from typing import List, Optional

from pygls.lsp.types import (
    Position,
)

from pygls.lsp import (
    CompletionItem,
    CompletionList,
)

from src.lsp.custom.config_definitions import LSPFeature
from src.lsp.custom.features import Feature


class Completer(Feature):
    def run(self, uri: str, cursor_position: Position) -> Optional[CompletionList]:
        if self.server.configuration is None:
            return None

        language_id = self.server.workspace.get_document(uri).language_id

        configs = self.server.custom.get_all_config_by(
            LSPFeature.completion, language_id
        )
        completions = []
        for _id, config in configs.items():
            self.config = config
            items = self.complete(uri, cursor_position)
            completions.extend(items)

        return CompletionList(
            is_incomplete=True,
            items=completions,
        )

    def complete(
        self, text_doc_uri: str, cursor_position: Position
    ) -> List[CompletionItem]:
        if self.config is None:
            return []

        word = self.get_word_under_cursor(text_doc_uri, cursor_position)

        output = self.run_cli_tool(
            self.config.command, text_doc_uri, word, cursor_position
        )
        items = []
        for line in output.splitlines():
            item = CompletionItem(label=line)
            items.append(item)

        return items

    def run_cli_tool(
        self,
        command: str,
        text_doc_uri: str,
        word: str,
        cursor_position: Position,
    ) -> str:
        # TODO: probably refactor into a list of Tuple pairs?
        command = command.replace("{file}", text_doc_uri.replace("file://", ""))
        command = command.replace("{word}", word)
        command = command.replace("{cursor_line}", str(cursor_position.line))
        command = command.replace("{cursor_char}", str(cursor_position.character))

        result = self.shell(command, text_doc_uri)
        return result.stdout.strip()

    def get_word_under_cursor(self, uri: str, cursor_position: Position):
        doc = self.server.workspace.get_document(uri)
        word = doc.word_at_position(cursor_position)
        return word
