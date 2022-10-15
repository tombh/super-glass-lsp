import pytest  # noqa

from pygls.lsp.types import Position

from src.lsp.server import CustomLanguageServer
from src.lsp.custom.completer import Completer
from src.lsp.custom.config import CLIToolConfig


# TODO: e2e test this:
# ... "command": [
#     "bash",
#     "-c",
#     # `{cursor_line}` and `{cursor_row}` should also be available
#     "cat {file} | tr -cs '[:alnum:]' '\n' | fzf --filter='{word}' | uniq",
# ]
def test_completer(mocker):
    cli_output = "\n".join(
        [
            "foo",
            "bar",
        ]
    )
    mocker.patch(
        "src.lsp.custom.completer.Completer.run_cli_tool", return_value=cli_output
    )
    mocker.patch(
        "src.lsp.custom.completer.Completer.get_word_under_cursor", return_value="fo"
    )

    server = CustomLanguageServer()
    completer = Completer(server)

    config_from_client = {
        "lsp_feature": "completion",
        "language_id": "testing",
        "command": [""],
        "parsing": {
            "formats": [
                # `{detail}` should also be available
                "{item}",
            ]
        },
    }
    config = CLIToolConfig(**config_from_client)

    completions = completer.complete(
        config, "path/to/file", Position(line=0, character=0)
    )

    assert len(completions) == 2

    assert completions[0].label == "foo"
    assert completions[1].label == "bar"
