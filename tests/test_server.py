import pytest  # noqa
import pytest_lsp  # noqa

import sys
import pathlib

import pygls.uris as uri
from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client


ROOT_PATH = pathlib.Path(__file__).parent / "workspace"
SERVER_CMD = [sys.executable, "super_glass_lsp/main.py"]


@pytest.mark.asyncio
async def test_initialization():
    root_uri = uri.from_fs_path(str(ROOT_PATH))

    cs_config = ClientServerConfig(
        server_command=SERVER_CMD,
        root_uri=root_uri,
        initialization_options={"foo": "bar"},
        client_factory=make_test_client,
    )

    cs = make_client_server(cs_config)
    try:
        response = await cs.start()

        # Check that basic file open/close support is enabled
        assert response["capabilities"]["textDocumentSync"]["openClose"]
        # That there are no surprising errors etc
        assert len(cs.client.messages) == 0

    finally:
        await cs.stop()
