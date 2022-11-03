import pytest  # noqa

from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.config_definitions import Config
from super_glass_lsp.lsp.custom.features import SubprocessOutput

from super_glass_lsp.lsp.custom.tests.utils import make_diagnostic


@pytest.mark.asyncio
async def test_supplying_multiple_output_formatters(mocker):
    cli_output = "\n".join(
        ["stdin:1:2 all", "stdin:11 no col", "stdin just the message"]
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        return_value=SubprocessOutput("", cli_output),
    )

    server = CustomLanguageServer()
    diagnoser = Diagnoser(server)

    config_from_client = {
        "lsp_feature": "diagnostic",
        "language_id": "testing",
        "command": "",
        "piped": False,
        "parsing": {
            "formats": [
                "stdin:{line:d}:{col:d} {msg}",
                "stdin:{line:d} {msg}",
                "stdin {msg}",
            ]
        },
    }
    diagnoser.config_id = "test_supplying_multiple_output_formatters"
    diagnoser.config = Config(**config_from_client)

    diagnostics = await diagnoser.diagnose("")

    assert len(diagnostics) == 3

    assert diagnostics[0].message == "all"
    assert diagnostics[0].range.start.line == 0
    assert diagnostics[0].range.start.character == 1

    assert diagnostics[1].message == "no col"
    assert diagnostics[1].range.start.line == 10
    assert diagnostics[1].range.start.character == 0

    assert diagnostics[2].message == "just the message"
    assert diagnostics[2].range.start.line == 0
    assert diagnostics[2].range.start.character == 0


@pytest.mark.asyncio
async def test_concurrent_diagnosers_dont_clobber(mocker):
    uri = "file:///"
    server = CustomLanguageServer()
    diagnoser = Diagnoser(server)
    server.config = config = {}
    config_from_client = {
        "lsp_feature": "diagnostic",
        "language_id": "testing",
        "piped": False,
    }

    config_from_client["command"] = "echo '1' >&2"
    config["foo"] = Config(**config_from_client)
    config_from_client["command"] = "echo '2' >&2"
    config["bar"] = Config(**config_from_client)
    mocker.patch(
        "super_glass_lsp.lsp.custom.hub.Hub.get_all_config_by",
        return_value=config,
    )

    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri=uri),
    )
    publisher = mocker.patch("pygls.server.LanguageServer.publish_diagnostics")

    await diagnoser.run(uri)

    diagnostic1 = make_diagnostic([0, 0, 0, 1], "1", "foo")
    diagnostic2 = make_diagnostic([0, 0, 0, 1], "2", "bar")
    publisher.assert_called_with(uri, [diagnostic1, diagnostic2])
