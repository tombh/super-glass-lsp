import typing
from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from pygls.lsp.types import MessageType


from ._base import Base
from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    Config,
    OutputParsingConfig,
    DEFAULT_FORMATTERS,
)


class Feature(Base):
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

    def get_parsing_config(
        self, default_formatters: List[str] = DEFAULT_FORMATTERS
    ) -> OutputParsingConfig:
        if (
            self.config.parsing is not None
            and self.config.parsing != OutputParsingConfig.default()
        ):
            config = self.config.parsing
        else:
            config = OutputParsingConfig(
                **typing.cast(Dict, {"formats": default_formatters})
            )
        return config

    def parsing_failed(self, output: str):
        summary = "Super Glass failed to parse shell output"
        command = f"Command: `{self.config.command}`"
        debug = f"{summary}\n{command}\nOutput: {output}"
        self.server.logger.warning(debug)
        self.server.show_message(debug, msg_type=MessageType.Warning)

    def cache_key(self):
        return f"{self.config_id}__{self.text_doc_uri}"

    def set_cache(self, items: Any):
        self.server.cache[self.cache_key()] = items

    def get_cache(self) -> Any:
        return self.server.cache[self.cache_key()]
