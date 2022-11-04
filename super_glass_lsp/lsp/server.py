import typing
from typing import Dict, Optional, Union, Any, List

import logging

from pygls.lsp.types import InitializeParams, Diagnostic
from pygls import server as pygls_server

from .custom.hub import Hub as CustomFeatures
from .custom.config_definitions import (
    Configs as CustomConfig,
)
from .custom.config_definitions import (
    InitializationOptions as CustomInitializationOptions,
)

from .custom.features._debounce import Debounce

Config = Optional[Union[CustomInitializationOptions, CustomConfig]]
"""
Illustrative that although initialization options and general config might be structurally similar,
you may have differing requirements for adherence. Eg, init options from the client may be sparse
and the general server config fills in the gaps with defaults.
"""


class CustomLanguageServer(pygls_server.LanguageServer):
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

        self.debounces: Dict[str, Debounce] = {}
        """
        Storage for debounce data.

        Often, but not always, it can be good to defer rapid requests on expensive code
        to a single aggregate request in the future.

        Diagnostics are a good candidate for debounces, as they're published as and when
        they're generated, rather than as direct responses to editor requests.
        """

        self.cache: Dict[str, List[Any]] = {}
        """
        Storage for response caches.

        Coupled with debouncing, it is sometimes necessary to reply to the editor with
        the last known state, rather than either do more expensive work or return nothing.
        Completion requests are a good example, as the editor always expects a direct and
        immediate response. If the response is empty, it display an empty completion list.
        Hence the value of caching.
        """

        self.diagnostics: Dict[str, List[Diagnostic]] = {}
        """
        Keep track of current diagnostics.

        It's reasonble that are various forms of diagnostics, each running in separate threads
        or processes. If we allow each source of diagnostics to publish directly to the editor
        then they will just clobber any other sources of diagnostics. Therefore, it is the server's
        responsibility to collate and publish what it perceives to be the entire aggregated state
        of diagnostics for a given file URI.
        """

    # TODO: Remove and put into `JsonRPCProtocol._handle_notification()`. See issue #227
    def add_feature(self, feature: str):
        """
        This is a wrapper just to catch and handle all unexpected errors in one place.

        TODO:
        Is this even useful? I wonder if this should be formally supported in Pygls itself?
        """

        def wrapper(func):
            @self.feature(feature)
            async def inner(*args, **kwargs):
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(e)
                    # TODO: should this have the name of the custom LSP server?
                    self.show_message(f"Unexpected error in LSP server: {e}")

            return inner

        return wrapper

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

        self.logger.info(f"Serialized config from editor: {self.config}")

        self.custom.initialize()

    @property
    def configuration(
        self,
    ) -> Optional[Config]:
        """Return the server's actual configuration."""
        return self.config

    def get_document_from_uri(self, uri: str):
        return self.workspace.get_document(uri)
