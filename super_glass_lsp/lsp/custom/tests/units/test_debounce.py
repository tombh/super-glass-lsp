import pytest  # noqa

import subprocess
import time

from pygls.workspace import Document
from pygls.lsp.types import Diagnostic, DiagnosticSeverity, Range, Position

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.config_definitions import Config


def test_debounce_restricts(mocker):
    cli_output = "\n".join(["stdin all"])
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri="file:///"),
    )
    mock = mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(
            [], stdout=cli_output, stderr="", returncode=0
        ),
    )

    server = CustomLanguageServer()
    diagnoser = Diagnoser(server)

    config_from_client = {
        "lsp_feature": "diagnostic",
        "language_id": "testing",
        "command": "",
        "piped": False,
        "parsing": {
            "formats": ["stdin {msg}"],
        },
    }
    diagnoser.server.config = {"testing": Config(**config_from_client)}
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=diagnoser.server.config,
    )

    for _ in range(10):
        diagnoser.run("")

    assert mock.call_count == 1


def test_debounce_releases(mocker):
    uri = "file:///"
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri=uri),
    )
    shell = mocker.patch(
        "subprocess.run",
        side_effect=[
            subprocess.CompletedProcess(
                [], stderr="stdin all", stdout="", returncode=0
            ),
            subprocess.CompletedProcess(
                [], stderr="stdin all different", stdout="", returncode=0
            ),
            subprocess.CompletedProcess(
                [], stderr="stdin all mooore", stdout="", returncode=0
            ),
        ],
    )
    publish = mocker.patch(
        "super_glass_lsp.lsp.server.CustomLanguageServer.publish_diagnostics"
    )

    server = CustomLanguageServer()
    diagnoser = Diagnoser(server)

    config_from_client = {
        "lsp_feature": "diagnostic",
        "language_id": "testing",
        "command": "",
        "piped": False,
        "debounce": 50,
        "parsing": {
            "formats": ["stdin {msg}"],
        },
    }
    diagnoser.server.config = {"testing": Config(**config_from_client)}
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=diagnoser.server.config,
    )

    diagnostic1 = Diagnostic(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=1),
        ),
        message="all",
        source="testing",
        severity=DiagnosticSeverity.Error,
    )
    diagnoser.run("")
    publish.assert_called_with(uri, [diagnostic1])

    time.sleep(0.1)

    diagnostic2 = Diagnostic(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=1),
        ),
        message="all different",
        source="testing",
        severity=DiagnosticSeverity.Error,
    )
    diagnoser.run("")
    publish.assert_called_with(uri, [diagnostic2])

    diagnoser.run("")
    publish.assert_called_with(uri, [])

    assert shell.call_count == 2
