import pytest  # noqa
import pytest_lsp  # noqa

from unittest.mock import MagicMock
from unittest.mock import patch

import asyncio

from pygls.lsp.methods import WORKSPACE_APPLY_EDIT
from pygls.lsp.types import ApplyWorkspaceEditParams

from super_glass_lsp.lsp.custom.tests.e2e.apps._utils import app_test
from pytest_lsp.client import Client


@app_test(
    "email_client",
    "inbox.md",
    patched_path="pygls.protocol.deserialize_params",
)
# TODO: Investigate what the situation is with Pygls and WorkspaceEdits.
# It seems that Pygls is only testing for receiving workspace edits from the client which
# I'm not sure makes much sense? This Dict patch converts a Pygls server from being able to
# receive a WorkspaceEdit response to being able to receive a Workspace Edit request.
# https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspace_applyEdit
# Ultimately I think this is fixed in the v1 branch?
@patch.dict(
    "pygls.lsp.LSP_METHODS_MAP",
    {
        WORKSPACE_APPLY_EDIT: (
            None,
            ApplyWorkspaceEditParams,
            None,
        )
    },
)
async def test_inbox_loads(client: Client, uri: str, patched: MagicMock):
    await asyncio.sleep(0.1)

    calls = patched.call_args_list
    args, _kwargs = calls[1]
    data = args[0]

    assert len(calls) == 2
    assert data["params"]["edit"]["documentChanges"][0]["edits"][0]["newText"] == "🤓"
