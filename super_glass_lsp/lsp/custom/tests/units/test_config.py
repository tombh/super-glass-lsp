import pytest  # noqa

from argparse import Namespace

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.config_definitions import LSPFeature


def test_config_merging():
    server = CustomLanguageServer()

    config_dict = {
        "configs": {
            "foobar": {
                "enabled": True,
                "lsp_feature": "diagnostic",
                "language_id": "testing",
                "command": "",
                "parsing": {
                    "formats": [
                        "stdin:{line:d}:{col:d} {msg}",
                        "stdin:{line:d} {msg}",
                        "stdin {msg}",
                    ]
                },
            }
        }
    }

    class params:
        initialization_options = config_dict

    server.initialize(params)

    assert len(server.config.configs) > 3


def test_app_config():
    server = CustomLanguageServer()
    server.cli_args = Namespace(app="email_client")

    class params:
        initialization_options = {}

    server.initialize(params)

    assert len(server.config.configs) > 1
    assert server.config.configs["inbox"].lsp_feature == LSPFeature.workspace_edit
