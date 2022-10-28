import pytest  # noqa
import pytest_lsp  # noqa

import sys
import pathlib

import pygls.uris as uri
from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client

from super_glass_lsp.lsp.custom import CUSTOM_SERVER_CONFIG_COMMAND

ROOT_PATH = pathlib.Path(__file__).parent / "workspace"
SERVER_CMD = [
    sys.executable,
    "super_glass_lsp/main.py",
    "--logfile",
    "lsp-server-test.log",
]


@pytest.mark.asyncio
async def test_initialization():
    root_uri = uri.from_fs_path(str(ROOT_PATH))

    cs_config = ClientServerConfig(
        server_command=SERVER_CMD,
        root_uri=root_uri,
        initialization_options={
            "configs": {
                "foobar": {
                    "lsp_feature": "diagnostic",
                    "language_id": "foo",
                    "command": "foo --bar",
                    "parsing": {
                        "formats": ["{msg} at line {line:d}, column {col:d}"],
                    },
                }
            }
        },
        client_factory=make_test_client,
    )

    cs = make_client_server(cs_config)
    try:
        await cs.start()

        configuration = await cs.client.execute_command_request(
            CUSTOM_SERVER_CONFIG_COMMAND
        )

        assert configuration["configs"]["markdownlint"]["language_id"] == "markdown"
        assert configuration["configs"]["foobar"]["language_id"] == "foo"

    finally:
        await cs.stop()
