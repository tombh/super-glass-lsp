import pytest  # noqa

import time

from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.config_definitions import Config
from super_glass_lsp.lsp.custom.features import SubprocessOutput

from super_glass_lsp.lsp.custom.tests.utils import make_diagnostic


@pytest.mark.asyncio
async def test_debounce_restricts(mocker):
    cli_output = "\n".join(["stdin all"])
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri="file:///"),
    )
    shell = mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        return_value=SubprocessOutput(cli_output, ""),
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
    diagnoser.server.config = {"test_debounce_restricts": Config(**config_from_client)}
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=diagnoser.server.config,
    )

    for _ in range(10):
        await diagnoser.run("")

    assert shell.call_count == 1


@pytest.mark.asyncio
async def test_debounce_releases(mocker):
    uri = "file:///"
    config_id = "test_debounce_releases"
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri=uri),
    )
    shell = mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        side_effect=[
            SubprocessOutput("", "stdin all"),
            SubprocessOutput("", "stdin all different"),
            SubprocessOutput("", "stdin all mooore"),
        ],
    )
    publisher = mocker.patch(
        "super_glass_lsp.lsp.server.CustomLanguageServer.publish_diagnostics"
    )

    server = CustomLanguageServer()
    server.config = {}
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
    config = {config_id: Config(**config_from_client)}
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=config,
    )

    await diagnoser.run(uri)
    diagnostic1 = make_diagnostic([0, 0, 0, 1], "all", config_id)
    publisher.assert_called_with(uri, [diagnostic1])

    time.sleep(0.1)

    await diagnoser.run(uri)
    diagnostic2 = make_diagnostic([0, 0, 0, 1], "all different", config_id)
    publisher.assert_called_with(uri, [diagnostic2])

    await diagnoser.run(uri)
    publisher.assert_called_with(uri, [])

    assert shell.call_count == 2
