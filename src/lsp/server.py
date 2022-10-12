import typing
from typing import Dict, Optional

import logging

from pygls.lsp.types import (
    InitializeParams,
)
from pygls.server import LanguageServer

from .custom import config as custom_config


class CustomLanguageServer(LanguageServer):
    """
    Pygls ``LanguageServer`` is the base class from which we can build our own custom
    language server.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_config: Optional[custom_config.InitializationOptions] = None
        """The user's configuration."""

        self.logger = logger or logging.getLogger(__name__)
        """The base logger that should be used for all language server log entries."""

    def initialize(self, params: InitializeParams):
        """
        This should be the very first request from the client/editor. It contains the
        user's configuration.
        """

        # Here we use the magic of Pydantic to automatically deserialize JSON data
        # using typed Python dictionaries
        self.user_config = custom_config.InitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )

    @property
    def configuration(self) -> Optional[custom_config.InitializationOptions]:
        """Return the server's actual configuration."""
        return self.user_config
