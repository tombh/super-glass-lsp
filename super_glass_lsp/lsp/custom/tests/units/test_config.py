import pytest  # noqa

from argparse import Namespace

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.config_definitions import LSPFeature


def _setup(mocker):
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_workspace_root",
        return_value="./",
    )


def test_config_merging(mocker):
    _setup(mocker)
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


def test_app_config(mocker):
    _setup(mocker)
    server = CustomLanguageServer()
    server.cli_args = Namespace(app="email_client")

    class params:
        initialization_options = {}

    server.initialize(params)

    assert len(server.config.configs) > 1
    assert server.config.configs["inbox"].lsp_feature == LSPFeature.workspace_edit


def test_config_is_unusable_with_missing_root_marker(mocker):
    _setup(mocker)
    server = CustomLanguageServer()
    config_dict = {
        "configs": {
            "foobar": {
                "enabled": True,
                "lsp_feature": "diagnostic",
                "root_markers": ["missing.txt"],
            }
        }
    }

    class params:
        initialization_options = config_dict

    server.initialize(params)

    all_config = server.custom.get_all_config_by(
        LSPFeature.diagnostic, "*", allow_missing_root_marker=True
    )
    assert "foobar" in all_config
    all_config = server.custom.get_all_config_by(LSPFeature.diagnostic, "*")
    assert "foobar" not in all_config
