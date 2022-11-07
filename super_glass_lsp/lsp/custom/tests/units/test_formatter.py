import pytest  # noqa

import time

from pygls.lsp.types import TextEdit, Position, Range

from super_glass_lsp.lsp.custom.features.formatter import Formatter
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

from ._utils import create_server


@pytest.mark.asyncio
async def test_formatter_debounce(mocker):
    outputs = [
        SubprocessOutput("\n".join(["foo1", "bar1"]), ""),
        SubprocessOutput("\n".join(["foo2", "bar2"]), ""),
    ]
    server, uri, _ = create_server(
        mocker,
        {
            "config1": {
                "lsp_feature": "formatter",
                "language_id": "testing",
                "debounce": 50,
            }
        },
        outputs,
        ""
    )

    expected = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=0),
        ),
        new_text=outputs[0].stdout,
    )
    actual = await Formatter.run_all(server, uri)
    assert actual == [expected]

    actual = await Formatter.run_all(server, uri)
    assert actual is None

    time.sleep(0.1)

    expected = TextEdit(
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=0),
        ),
        new_text=outputs[1].stdout,
    )
    actual = await Formatter.run_all(server, uri)
    assert actual == [expected]
