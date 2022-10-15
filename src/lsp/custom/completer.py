from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

import subprocess

from pygls.lsp.types import (
    Position,
)

from pygls.lsp import (
    CompletionItem,
    CompletionList,
)

from .config import CLIToolConfig, LSPFeature


class Completer:
    # TODO: refactor into shared parent class
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        # TODO: use the name of the CLI tool
        self.name = type(server).__name__

    def run(self, uri: str, cursor_position: Position) -> Optional[CompletionList]:
        if self.server.configuration is None:
            return None

        language_id = self.server.workspace.get_document(uri).language_id

        configs = self.server.configuration.get_all_by(
            LSPFeature.completion, language_id
        )
        completions = []
        for _id, config in configs.items():
            items = self.complete(config, uri, cursor_position)
            completions.extend(items)

        return CompletionList(
            is_incomplete=True,
            items=completions,
        )

    def complete(
        self, config: CLIToolConfig, text_doc_uri: str, cursor_position: Position
    ) -> List[CompletionItem]:
        word = self.get_word_under_cursor(text_doc_uri, cursor_position)

        output = self.run_cli_tool(config.command, text_doc_uri, word, cursor_position)
        items = []
        for line in output.splitlines():
            item = CompletionItem(label=line)
            items.append(item)

        return items

    def run_cli_tool(
        self,
        command_with_tokens: List[str],
        text_doc_uri: str,
        word: str,
        cursor_position: Position,
    ) -> str:
        command = []
        for item in command_with_tokens:
            # TODO: probably refactor into a list of Tuple pairs?
            item = item.replace("{file}", text_doc_uri.replace("file://", ""))
            item = item.replace("{word}", word)
            item = item.replace("{cursor_line}", str(cursor_position.line))
            item = item.replace("{cursor_char}", str(cursor_position.character))
            command.append(item)

        self.server.logger.debug(f"command: {command}")

        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

        # TODO: check for failure

        return result.stdout.strip()

    def get_word_under_cursor(self, uri: str, cursor_position: Position):
        doc = self.server.workspace.get_document(uri)
        word = doc.word_at_position(cursor_position)
        return word
