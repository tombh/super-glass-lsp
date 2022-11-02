import pytest  # noqa

from pygls.workspace import Document

from super_glass_lsp.lsp.server import CustomLanguageServer
from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.config_definitions import Config
from super_glass_lsp.lsp.custom.features import SubprocessOutput


@pytest.mark.asyncio
async def test_supplying_multiple_output_formatters(mocker):
    cli_output = "\n".join(
        ["stdin:1:2 all", "stdin:11 no col", "stdin just the message"]
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature._subprocess_run",
        return_value=SubprocessOutput("", cli_output),
    )
    mocker.patch(
        "super_glass_lsp.lsp.custom.features.Feature.get_document_from_uri",
        return_value=Document(language_id="testing", uri="file:///"),
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

    diagnostics = await diagnoser.diagnose("", diagnoser.config)

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
