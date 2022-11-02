import pytest  # noqa

import time

from pygls.lsp.types import TextEdit, Position, Range
from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.formatter import Formatter
from super_glass_lsp.lsp.custom.config_definitions import Config
from super_glass_lsp.lsp.custom.features import SubprocessOutput


@pytest.mark.asyncio
async def test_formatter_debounce(mocker):
    output1 = "\n".join(["foo1", "bar1"])
    output2 = "\n".join(["foo2", "bar2"])
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
            SubprocessOutput(output1, ""),
            SubprocessOutput(output2, ""),
        ],
    )

    server = CustomLanguageServer()
    formatter = Formatter(server)
    formatter.config_id = "testing"

    config_from_client = {
        "lsp_feature": "formatter",
        "language_id": "testing",
        "command": "",
        "debounce": 50,
    }
    formatter.server.config = {"test_formatter_debounce": Config(**config_from_client)}
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=formatter.server.config,
    )

    expected = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=2, character=0),
        ),
        new_text=output1,
    )
    actual = await formatter.run("path/to/file")
    assert actual == [expected]

    actual = await formatter.run("path/to/file")
    assert actual is None

    time.sleep(0.1)

    expected = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=2, character=0),
        ),
        new_text=output2,
    )
    actual = await formatter.run("path/to/file")
    assert actual == [expected]
