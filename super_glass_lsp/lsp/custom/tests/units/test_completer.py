import pytest  # noqa

from pygls.lsp.types import Position

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.completer import Completer
from super_glass_lsp.lsp.custom.config_definitions import Config


def test_completer(mocker):
    cli_output = "\n".join(
        [
            "foo",
            "bar",
        ]
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.completer.Completer.run_cli_tool",
        return_value=cli_output,
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.completer.Completer.get_word_under_cursor",
        return_value="fo",
    )

    server = CustomLanguageServer()
    completer = Completer(server)

    config_from_client = {
        "lsp_feature": "completion",
        "language_id": "testing",
        "command": "",
    }
    completer.config = Config(**config_from_client)

    completions = completer.complete("path/to/file", Position(line=0, character=0))

    assert len(completions) == 2

    assert completions[0].label == "foo"
    assert completions[1].label == "bar"
