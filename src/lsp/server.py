import typing
from typing import Dict, Optional, Union

import logging

from pygls.lsp.types import (
    InitializeParams,
)
from pygls import server

from .custom.hub import Hub as CustomFeatures
from .custom.config_definitions import (
    CLIToolConfigs as CustomConfig,
)
from .custom.config_definitions import (
    InitializationOptions as CustomInitializationOptions,
)

Config = Optional[Union[CustomInitializationOptions, CustomConfig]]


class CustomLanguageServer(server.LanguageServer):
    """
    Pygls' ``LanguageServer`` is the base class from which we can build our own custom
    language server.

    Typically, this class could just be merged with ``custom.hub.Hub``, but in order to keep
    the specific implementation code separate ``CustomLanguageServer`` and ``custom.hub.Hub`` are 2
    distinct classes.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config: Config = None
        """The user's configuration."""

        self.logger = logger or logging.getLogger(__name__)
        """The base logger that should be used for all language server log entries."""

        # TODO: recursive access to each other?? (seems ok)
        self.custom: CustomFeatures = CustomFeatures(self)
        """
        Custom functionality that would usually live in this class, but is being kept
        separate for educational purposes.
        """

    def initialize(self, params: InitializeParams):
        """
        This should be the very first request from the client/editor. It contains the
        user's configuration.
        """

        # Here we use the magic of Pydantic to automatically deserialize JSON data
        # using typed Python dictionaries
        self.config = CustomInitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )

        self.custom.initialize()

    @property
    def configuration(
        self,
    ) -> Optional[Config]:
        """Return the server's actual configuration."""
        return self.config
