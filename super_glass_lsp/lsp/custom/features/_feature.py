import typing
from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from pygls.lsp.types import Range, Position

from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    Config,
    ShellCommand,
)
from ._subprocess import Subprocess, SubprocessOutput


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

    async def shell(self, check: bool = True) -> SubprocessOutput:
        if isinstance(self.command, list):
            raise Exception("Command arrays not suported")

        command = self.command

        if self.text_doc_uri is not None:
            command = command.replace(
                "{file}", self.text_doc_uri.replace("file://", "")
            )

        if self.server.workspace is not None:
            command = command.replace(
                "{workspace_root}", self.server.workspace.root_path
            )

        input = None
        if self.config.piped and self.text_doc_uri is not None:
            document = self.get_current_document()
            input = document.source

        debug = {
            "text_doc_uri": self.text_doc_uri,
            "tool_config": self.config,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        output = await Subprocess.run(self.server, self.config, command, input, check)
        return output

    def parse_range(
        self, start_line: int, start_char: int, end_line: int, end_char: int
    ):
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
        return self.parse_range(0, 0, -1, -1)

    def get_current_document(self):
        if self.text_doc_uri is None:
            raise Exception

        return self.server.get_document_from_uri(self.text_doc_uri)
