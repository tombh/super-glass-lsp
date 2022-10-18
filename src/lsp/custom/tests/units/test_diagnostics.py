import pytest  # noqa

from src.lsp.server import CustomLanguageServer
from src.lsp.custom.features.diagnoser import Diagnoser
from src.lsp.custom.config_definitions import CLIToolConfig


def test_supplying_multiple_output_formatters(mocker):
    cli_output = "\n".join(
        ["stdin:1:2 all", "stdin:11 no col", "stdin just the message"]
    )
    mocker.patch(
        "src.lsp.custom.features.diagnoser.Diagnoser.run_cli_tool",
        return_value=cli_output,
    )

    server = CustomLanguageServer()
    diagnoser = Diagnoser(server)

    config_from_client = {
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
    config = CLIToolConfig(**config_from_client)

    diagnostics = diagnoser.diagnose("", config)

    assert len(diagnostics) == 3

    assert diagnostics[0].message == "all"
    assert diagnostics[0].range.start.line == 1
    assert diagnostics[0].range.start.character == 2

    assert diagnostics[1].message == "no col"
    assert diagnostics[1].range.start.line == 11
    assert diagnostics[1].range.start.character == 0

    assert diagnostics[2].message == "just the message"
    assert diagnostics[2].range.start.line == 0
    assert diagnostics[2].range.start.character == 0
