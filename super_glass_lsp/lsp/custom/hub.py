import typing
from typing import TYPE_CHECKING, Optional, Dict

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import os
from argparse import ArgumentParser

import yaml  # type: ignore
from mergedeep import merge  # type: ignore
from pygls.lsp.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
)
from pygls.lsp import CompletionParams, CompletionList, DocumentFormattingParams

from super_glass_lsp.lsp.custom import config_definitions
from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    Config,
)
from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.features.completer import Completer
from super_glass_lsp.lsp.custom.features.formatter import (
    Formatter,
    SuperGlassFormatResult,
)
from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit

DEFAULT_CONFIG_PATH = os.path.join("..", "..", "config.default.yaml")
DEFAULT_APP_CONFIG_PATH = "apps"


class Hub:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

    def initialize(self):
        if "app" not in self.server.cli_args or self.server.cli_args.app is None:
            self.merge_config()
        else:
            self.load_app_config(self.server.cli_args.app)

        self.start_daemons()

    def add_cli_args(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--app", help="Name of app config to run")
        return parser

    def get_all_config_by(
        self, feature: LSPFeature, language: Optional[str]
    ) -> Dict[str, Config]:
        if self.server.config is None:
            self.server.logger.warning("`server.config` not set")
            return {}

        filtered_config: Dict[str, Config] = {}
        for id, config in self.server.config.configs.items():
            self.server.logger.debug(f"Got config: {[id, config]}")
            # In order to fully use the type system it might be possible to do this with `TypeVar`
            # See: https://stackoverflow.com/a/66700544
            is_feature = config.lsp_feature == feature  # type: ignore
            is_language = config.language_id == language  # type: ignore
            if config.enabled and is_feature and is_language:
                filtered_config[id] = config  # type: ignore

        return filtered_config

    @classmethod
    def load_default_config(cls) -> Dict:
        return Hub.load_config(DEFAULT_CONFIG_PATH)

    @classmethod
    def load_config(cls, file_path: str) -> Dict:
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, file_path)
        file = open(filename)
        contents = file.read()
        config_dict = yaml.load(contents, Loader=yaml.Loader)
        return config_dict

    def load_app_config(self, name: str):
        path = os.path.join(DEFAULT_APP_CONFIG_PATH, f"{name}.yaml")
        config_dict = Hub.load_config(path)
        self.server.config = config_definitions.Configs(
            **typing.cast(Dict, config_dict)
        )
        self.server.logger.debug(f"App config loaded: {self.server.config}")
        return config_dict

    def merge_config(self):
        default_config_raw = Hub.load_default_config()
        user_configs = {}

        for id, config in self.server.config.configs.items():
            self.server.logger.debug(f"Removing `None`s from '{id}': {config}")
            user_configs[id] = {k: v for k, v in config.dict().items() if v is not None}
            self.server.logger.debug(f"Removed `None`s from '{id}': {config}")

            # TODO: think about not allowing `lsp_feature` to be overriden?

        final_config = merge({}, default_config_raw, {"configs": user_configs})
        self.server.config = config_definitions.InitializationOptions(
            **typing.cast(Dict, final_config)
        )

        self.server.logger.debug(f"Final merged config: {self.server.config}")

    def start_daemons(self):
        WorkspaceEdit.start_all_daemons(self.server)

    async def did_change(self, params: DidChangeTextDocumentParams):
        await Diagnoser.run_all(self.server, params.text_document.uri)

    async def did_open(self, params: DidOpenTextDocumentParams):
        await Diagnoser.run_all(self.server, params.text_document.uri)

    async def completion_request(
        self, params: CompletionParams
    ) -> Optional[CompletionList]:
        return await Completer.run_all(
            self.server, params.text_document.uri, params.position
        )

    async def formatting_request(
        self, params: DocumentFormattingParams
    ) -> SuperGlassFormatResult:
        return await Formatter.run_all(self.server, params.text_document.uri)
