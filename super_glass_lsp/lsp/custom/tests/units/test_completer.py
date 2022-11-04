import pytest  # noqa

from pygls.lsp.types import Position

from super_glass_lsp.lsp.custom.features.completer import Completer
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

from ._utils import create_server


@pytest.mark.asyncio
async def test_completer(mocker):
    outputs = [
        SubprocessOutput("foo\nbar", ""),
    ]
    config = {
        "config1": {
            "lsp_feature": "completion",
            "language_id": "testing",
        },
    }
    server, uri, subprocess_mock = create_server(
        mocker,
        config,
        outputs,
    )

    completions = await Completer.run_all(server, uri, Position(line=0, character=0))
    assert len(completions.items) == 2
    assert completions.items[0].label == "foo"
    assert completions.items[1].label == "bar"


@pytest.mark.asyncio
async def test_completer_debounce_cache(mocker):
    outputs = [
        SubprocessOutput("foo1\nbar1", ""),
        SubprocessOutput("foo2\nba2", ""),
    ]
    config = {
        "config1": {
            "lsp_feature": "completion",
            "language_id": "testing",
        },
    }
    server, uri, subprocess_mock = create_server(
        mocker,
        config,
        outputs,
    )

    completions = await Completer.run_all(server, uri, Position(line=0, character=0))
    assert len(completions.items) == 2
    assert completions.items[0].label == "foo1"
    assert completions.items[1].label == "bar1"

    completions = await Completer.run_all(server, uri, Position(line=0, character=0))
    assert len(completions.items) == 2
    assert completions.items[0].label == "foo1"
    assert completions.items[1].label == "bar1"
