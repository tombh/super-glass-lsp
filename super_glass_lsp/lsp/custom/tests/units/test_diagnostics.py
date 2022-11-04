import pytest  # noqa

from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

from super_glass_lsp.lsp.custom.tests.utils import make_diagnostic

from ._utils import create_server


@pytest.mark.asyncio
async def test_supplying_multiple_output_formatters(mocker):
    outputs = [
        SubprocessOutput(
            "",
            "\n".join(["stdin:1:2 all", "stdin:11 no col", "stdin just the message"]),
        ),
    ]
    config = {
        "config1": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
            "command": "",
            "parsing": {
                "formats": [
                    "stdin:{line:d}:{col:d} {msg}",
                    "stdin:{line:d} {msg}",
                    "stdin {msg}",
                ]
            },
        }
    }
    server, uri, _ = create_server(
        mocker,
        config,
        outputs,
    )

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]

    assert len(diagnostics) == 3
    assert diagnostics[0] == make_diagnostic([0, 1, 0, 2], "all", "config1")
    assert diagnostics[1] == make_diagnostic([10, 0, 10, 1], "no col", "config1")
    assert diagnostics[2] == make_diagnostic(
        [0, 0, 0, 1], "just the message", "config1"
    )


@pytest.mark.asyncio
async def test_concurrent_diagnosers_dont_clobber(mocker):
    outputs = [
        SubprocessOutput("", "1"),
        SubprocessOutput("", "2"),
    ]
    config = {
        "config1": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
            "piped": False,
        },
        "config2": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
            "piped": False,
        },
    }
    server, uri, _ = create_server(
        mocker,
        config,
        outputs,
    )

    await Diagnoser.run_all(server, uri)
    diagnostics1 = server.diagnostics["config1"]
    diagnostics2 = server.diagnostics["config2"]

    assert diagnostics1[0] == make_diagnostic([0, 0, 0, 1], "1", "config1")
    assert diagnostics2[0] == make_diagnostic([0, 0, 0, 1], "2", "config2")
