import typing
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Tuple

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import re
from parse import parse  # type: ignore

from pygls.workspace import position_from_utf16
from pygls.lsp.types import Range, Position

from ._subprocess import Subprocess, SubprocessOutput
from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    Config,
    ShellCommand,
)


Replacements = List[Tuple[str, str]]


class Feature:
    def __init__(
        self,
        server: "CustomLanguageServer",
        config_id: str,
        text_doc_uri: Optional[str],
    ):
        if (
            server.configuration is None
            or config_id not in server.configuration.configs
        ):
            raise Exception(f"`config_id` '{config_id}' not found in server config")

        self.server = server
        self.config_id: str = config_id
        self.text_doc_uri: Optional[str] = text_doc_uri
        # TODO: Would be better if we didn't have to do this typecasting
        self.config: Config = Config(
            **typing.cast(Dict, server.configuration.configs[config_id].dict())
        )
        self.command: ShellCommand = self.config.command

    @property
    def name(self):
        return self.config_id

    @property
    def debouncer(self):
        return self.server.debounces[self.cache_key()]

    @classmethod
    def get_configs(
        cls, server: "CustomLanguageServer", text_doc_uri: str, feature: LSPFeature
    ):
        document = server.get_document_from_uri(text_doc_uri)
        all = server.custom.get_all_config_by(feature, document.language_id)
        configs: Dict[str, Config] = {}
        for id, config in all.items():
            if document.language_id != config.language_id:
                continue
            configs[id] = config
        return configs

    def cache_key(self):
        return f"{self.config_id}__{self.text_doc_uri}"

    def set_cache(self, items: Any):
        self.server.cache[self.cache_key()] = items

    def get_cache(self) -> Any:
        return self.server.cache[self.cache_key()]

    def resolve_commands(self, replacements: Replacements) -> ShellCommand:
        resolved: ShellCommand
        commands = self.command
        if isinstance(commands, list):
            resolved = []
            for command in commands:
                resolved.append(self.replace_tokens(command, replacements))
        else:
            resolved = self.replace_tokens(commands, replacements)

        return resolved

    def replace_tokens(self, string: str, replacements: Replacements) -> str:
        for replacement in replacements:
            string = string.replace(replacement[0], replacement[1])
        return string

    async def run_pre_commands(
        self,
        commands: ShellCommand,
    ):
        format = "call {config_id} {args}"

        if not isinstance(commands, list):
            return

        pre_commands = commands[:-1]

        if len(pre_commands) == 0:
            self.server.logger.warning(
                "Feature.run_pre_commands expected a list of commands but didn't find any"
            )
            return

        for command in pre_commands:
            result = await self.shell(command)
            if result.stdout == "":
                self.server.logger.warning("No output to parse from pre-command")
                continue
            parsed = parse(format, result.stdout)
            if parsed is not None:
                args = parsed["args"].strip()
            else:
                args = ""
                parsed = parse("call {config_id}", result.stdout)
                if parsed is None:
                    raise Exception(f"Couldn't parse output from pre-command: {result}")

            # TODO: at least diagnostic notifications could be supported as pre-commands too
            from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit

            workspace_edit = WorkspaceEdit(self.server, parsed["config_id"].strip())
            if self.text_doc_uri is None:
                raise Exception(
                    "WorkspaceEdit called as pre-command must have text_doc_uri"
                )
            workspace_edit.text_doc_uri = self.text_doc_uri
            await workspace_edit.run_once(args)

    async def shell(self, command: str, check: bool = True) -> SubprocessOutput:
        if self.text_doc_uri is not None:
            command = command.replace(
                "{file}", self.text_doc_uri.replace("file://", "")
            )
            command = command.replace("{uri}", self.text_doc_uri)

        if self.server.workspace is not None:
            command = command.replace(
                "{workspace_root}", self.server.workspace.root_path
            )

        input = None
        if self.config.piped and self.text_doc_uri is not None:
            document = self.get_current_document()
            input = document.source
            self.server.logger.debug("Piping the following to STDIN:")
            self.server.logger.debug(input)

        debug = {
            "text_doc_uri": self.text_doc_uri,
            "tool_config": self.config,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        output = await Subprocess.run(self.server, self.config, command, input, check)
        output.stdout = output.stdout.strip()
        output.stderr = output.stderr.strip()
        return output

    def parse_range(
        self, start_line: int, start_char: int, end_line: int, end_char: int
    ):
        """
        Parses something like `0:0,23:3` to produce a "selection" range in a document
        """
        if self.text_doc_uri is None:
            raise Exception

        if int(end_line) == -1:
            current_document = self.get_current_document()
            end_line = len(current_document.lines)

        if int(end_char) == -1:
            # NB:
            # `end_char` may need to use something like pygls.workspace.utf16_num_units(lines[-1])
            # in order to handle wide characters. I have seen some weirdness like a single char
            # being copied on every save. But it's hard to know what's going on behind the scenes.
            end_char = 0

        return Range(
            start=Position(line=start_line, character=start_char),
            end=Position(line=end_line, character=end_char),
        )

    def range_for_whole_document(self):
        """
        `0:0,-1:1` has the special meaning of: select the whole document.

        This is not a LSP convention.
        """
        return self.parse_range(0, 0, -1, -1)

    def get_current_document(self):
        if self.text_doc_uri is None:
            raise Exception

        return self.server.get_document_from_uri(self.text_doc_uri)

    def get_wordish_under_cursor(self, cursor_position: Position):
        """
        Get anything between whitespace
        """
        if self.text_doc_uri is None:
            raise Exception
        doc = self.server.get_document_from_uri(self.text_doc_uri)
        # Doesn't start with whitespace
        re_start_word = re.compile(r"[^\s]*$")
        # Doesn't end with whitespace
        re_end_word = re.compile(r"^[^\s]*")
        word = doc.word_at_position(
            cursor_position, re_start_word=re_start_word, re_end_word=re_end_word
        )
        return word

    def get_line_under_cursor(self, cursor_position: Position):
        if self.text_doc_uri is None:
            raise Exception
        doc = self.server.get_document_from_uri(self.text_doc_uri)
        lines = doc.lines
        if cursor_position.line >= len(lines):
            return ""

        row, _ = position_from_utf16(lines, cursor_position)
        line = lines[row]
        return line
