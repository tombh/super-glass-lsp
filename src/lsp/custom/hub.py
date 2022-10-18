import os
import yaml  # type: ignore
from mergedeep import merge  # type: ignore

import typing
from typing import TYPE_CHECKING, Optional, Dict

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)

from pygls.lsp import (
    CompletionParams,
    CompletionList,
)

from src.lsp.custom import config_definitions
from src.lsp.custom.config_definitions import (
    LSPFeature,
    CLIToolConfig,
)
from src.lsp.custom.features.diagnoser import Diagnoser
from src.lsp.custom.features.completer import Completer

DEFAULT_CONFIG_PATH = "../../config.default.yaml"


class Hub:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

    def initialize(self):
        self.merge_config()

    def get_all_config_by(
        self, feature: LSPFeature, language: Optional[str]
    ) -> Dict[str, CLIToolConfig]:
        if self.server.config is None:
            return {}

        filtered_config: Dict[str, CLIToolConfig] = {}
        for id, config in self.server.config.configs.items():
            # In order to fully use the type system it might be possible to do this with `TypeVar`
            # See: https://stackoverflow.com/a/66700544
            is_feature = config.lsp_feature == feature  # type: ignore
            is_language = config.language_id == language  # type: ignore
            if config.enabled and is_feature and is_language:
                filtered_config[id] = config  # type: ignore

        return filtered_config

    @classmethod
    def load_default_config(cls) -> Dict:
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, DEFAULT_CONFIG_PATH)
        file = open(filename)
        contents = file.read()
        default_config_dict = yaml.load(contents, Loader=yaml.Loader)
        return default_config_dict

    def merge_config(self):
        default_config_raw = Hub.load_default_config()

        config = merge({}, default_config_raw, self.server.config.dict())

        self.server.config = config_definitions.InitializationOptions(
            **typing.cast(Dict, config)
        )

    def did_change(self, params: DidChangeTextDocumentParams):
        diagnoser = Diagnoser(self.server)
        diagnoser.run(params.text_document.uri)

    def did_open(self, params: DidOpenTextDocumentParams):
        diagnoser = Diagnoser(self.server)
        diagnoser.run(params.text_document.uri)

    def completion_request(self, params: CompletionParams) -> Optional[CompletionList]:
        completer = Completer(self.server)
        return completer.run(params.text_document.uri, params.position)
