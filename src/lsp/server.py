import typing
from typing import Dict, Optional


from pygls.lsp.types import (
    InitializeParams,
)
from pygls.server import LanguageServer

from .custom import config as custom_config


class CustomLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()

        self.user_config: Optional[custom_config.InitializationOptions] = None
        """The user's configuration."""

    def initialize(self, params: InitializeParams):
        self.user_config = custom_config.InitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )

    @property
    def configuration(self) -> Optional[custom_config.InitializationOptions]:
        """Return the server's actual configuration."""
        return self.user_config
