import pytest  # noqa

from src.lsp.definition import CLIToolsLanguageServer
from src.lsp.diagnoser import Diagnoser
from src.lsp.clitool_config import CLIToolConfig


def test_supplying_multiple_output_formatters(mocker):
    cli_output = "\n".join(
        ["stdin:1:2 all", "stdin:11 no col", "stdin just the message"]
    )
    mocker.patch("src.lsp.diagnoser.Diagnoser.run_cli_tool", return_value=cli_output)

    server = CLIToolsLanguageServer()
    diagnoser = Diagnoser(server)

    client_config = {
        "language_id": "testing",
        "command": [""],
        "parsing": {
            "formats": [
                "stdin:{line:d}:{col:d} {msg}",
                "stdin:{line:d} {msg}",
                "stdin {msg}",
            ]
        },
    }
    config = CLIToolConfig(**client_config)

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
