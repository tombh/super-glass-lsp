import typing
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from super_glass_lsp.lsp.custom.config_definitions import (
    Config,
    ShellCommand,
)


class Base:
    def __init__(
        self,
        server: "CustomLanguageServer",
        config_id: str,
        text_doc_uri: Optional[str] = None,
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
