import pytest  # noqa

import time
import subprocess

from pygls.lsp.types import TextEdit, Position, Range
from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.formatter import Formatter
from super_glass_lsp.lsp.custom.config_definitions import Config


def test_formatter_debounce(mocker):
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
        "subprocess.run",
        side_effect=[
            subprocess.CompletedProcess([], stdout=output1, stderr="", returncode=0),
            subprocess.CompletedProcess([], stdout=output2, stderr="", returncode=0),
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
    formatter.server.config = {"testing": Config(**config_from_client)}
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
    actual = formatter.run("path/to/file")
    assert actual == [expected]

    actual = formatter.run("path/to/file")
    assert actual is None

    time.sleep(0.1)

    expected = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=2, character=0),
        ),
        new_text=output2,
    )
    actual = formatter.run("path/to/file")
    assert actual == [expected]
