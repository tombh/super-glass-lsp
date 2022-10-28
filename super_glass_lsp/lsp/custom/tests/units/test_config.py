import pytest  # noqa

from super_glass_lsp.lsp.server import CustomLanguageServer


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
