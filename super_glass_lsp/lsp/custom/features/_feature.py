import typing
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from super_glass_lsp.lsp.custom.config_definitions import Config
from ._subprocess import Subprocess, SubprocessOutput


class Feature:
    def __init__(
        self, server: "CustomLanguageServer", config_id: str, text_doc_uri: str
    ):
        if (
            server.configuration is None
            or config_id not in server.configuration.configs
        ):
            raise Exception(f"`config_id` '{config_id}' not found in server config")

        self.server = server
        self.config_id: str = config_id
        self.text_doc_uri: str = text_doc_uri
        # TODO: Would be better if we didn't have to do this typecasting
        self.config: Config = Config(
            **typing.cast(Dict, server.configuration.configs[config_id].dict())
        )
        self.command: str = self.config.command

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
        command = self.command.replace(
            "{file}", self.text_doc_uri.replace("file://", "")
        )

        input = None
        if self.config.piped and self.text_doc_uri is not None:
            document = self.server.get_document_from_uri(self.text_doc_uri)
            input = document.source

        debug = {
            "text_doc_uri": self.text_doc_uri,
            "tool_config": self.config,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        output = await Subprocess.run(self.server, self.config, command, input, check)
        return output
