import pytest  # noqa

from pygls.lsp.types import Position
from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.completer import Completer
from super_glass_lsp.lsp.custom.config_definitions import Config
from super_glass_lsp.lsp.custom.features import SubprocessOutput


@pytest.mark.asyncio
async def test_completer(mocker):
    cli_output = "\n".join(
        [
            "foo",
            "bar",
        ]
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri="file:///"),
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        return_value=SubprocessOutput(cli_output, ""),
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.completer.Completer.get_word_under_cursor",
        return_value="fo",
    )

    server = CustomLanguageServer()
    completer = Completer(server)
    completer.config_id = "test_completer"

    config_from_client = {
        "lsp_feature": "completion",
        "language_id": "testing",
        "command": "",
        "piped": False,
    }
    completer.config = Config(**config_from_client)

    completions = await completer.complete(
        "path/to/file", Position(line=0, character=0)
    )

    assert len(completions) == 2

    assert completions[0].label == "foo"
    assert completions[1].label == "bar"


@pytest.mark.asyncio
async def test_completer_debounce_cache(mocker):
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri="file:///"),
    )
    mocker.patch(
        "pygls.workspace.Document.source",
        return_value="",
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        side_effect=[
            SubprocessOutput(
                "\n".join(["foo1", "bar1"]),
                "",
            ),
            SubprocessOutput(
                "\n".join(["foo2", "bar2"]),
                "",
            ),
        ],
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.completer.Completer.get_word_under_cursor",
        return_value="fo",
    )

    server = CustomLanguageServer()
    completer = Completer(server)
    completer.config_id = "test_completer_debounce_cache"

    config_from_client = {
        "lsp_feature": "completion",
        "language_id": "testing",
        "command": "",
    }
    completer.config = Config(**config_from_client)

    completions = await completer.complete(
        "path/to/file", Position(line=0, character=0)
    )
    assert len(completions) == 2
    assert completions[0].label == "foo1"
    assert completions[1].label == "bar1"

    completions = await completer.complete(
        "path/to/file", Position(line=0, character=0)
    )
    assert len(completions) == 2
    assert completions[0].label == "foo1"
    assert completions[1].label == "bar1"
