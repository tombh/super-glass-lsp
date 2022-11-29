import pytest  # noqa
import pytest_lsp  # noqa

from unittest.mock import MagicMock

import asyncio

from super_glass_lsp.lsp.custom.tests.e2e.apps._utils import app_test
from pytest_lsp.client import Client


@pytest.mark.timeout(10)
@app_test(
    "email_client",
    "inbox.md",
    patched_path="pygls.protocol.deserialize_params",
)
async def test_inbox_loads(client: Client, uri: str, patched: MagicMock):
    pause = 0.1
    waited = 0.0
    max_wait = 8
    while True:
        waited = waited + pause
        if waited > max_wait:
            assert False, "Timeout waiting for LSP server to send applyEdit request"
        calls = patched.call_args_list
        if len(calls) == 2:
            break
        await asyncio.sleep(pause)

    args, _kwargs = calls[1]
    data = args[0]
    body = data["params"]["edit"]["documentChanges"][0]["edits"][0]["newText"]
    assert "# Inbox" in body
    assert "| Google" in body
