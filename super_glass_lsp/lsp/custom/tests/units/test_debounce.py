import pytest  # noqa

import time
import asyncio

from super_glass_lsp.lsp.custom.features.diagnoser import Diagnoser
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

from super_glass_lsp.lsp.custom.tests.utils import make_diagnostic

from ._utils import create_server


@pytest.mark.asyncio
async def test_debounce_restricts(mocker):
    outputs = [
        SubprocessOutput("", "1"),
    ]
    config = {
        "config1": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
        },
    }
    server, uri, subprocess_mock = create_server(
        mocker,
        config,
        outputs,
    )

    for _ in range(10):
        await Diagnoser.run_all(server, uri)

    assert subprocess_mock.call_count == 1


@pytest.mark.asyncio
async def test_debounce_releases(mocker):
    outputs = [
        SubprocessOutput("", "all"),
        SubprocessOutput("", "all different"),
        SubprocessOutput("", "all moore"),
    ]
    config = {
        "config1": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
            "debounce": 50,
        },
    }
    server, uri, subprocess_mock = create_server(
        mocker,
        config,
        outputs,
    )

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all", "config1")

    time.sleep(0.1)

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all different", "config1")

    time.sleep(0)

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all different", "config1")

    assert subprocess_mock.call_count == 2


@pytest.mark.asyncio
async def test_debounce_defers(mocker):
    outputs = [
        SubprocessOutput("", "all"),
        SubprocessOutput("", "all different"),
    ]
    config = {
        "config1": {
            "lsp_feature": "diagnostic",
            "language_id": "testing",
            "debounce": 50,
        },
    }
    server, uri, subprocess_mock = create_server(
        mocker,
        config,
        outputs,
    )

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all", "config1")

    time.sleep(0)

    await Diagnoser.run_all(server, uri)
    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all", "config1")

    await asyncio.sleep(0.1)

    diagnostics = server.diagnostics["config1"]
    assert diagnostics[0] == make_diagnostic([0, 0, 0, 1], "all different", "config1")

    assert subprocess_mock.call_count == 2
