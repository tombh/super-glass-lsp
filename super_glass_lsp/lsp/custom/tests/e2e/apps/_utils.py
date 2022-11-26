import pytest  # noqa
import sys
import pathlib

import pygls.uris as uri
from pygls.lsp.methods import WORKSPACE_APPLY_EDIT

from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client

SERVER_CMD_BASE = [
    "timeout",
    "30",
    sys.executable,
    "super_glass_lsp/main.py",
    "--logfile",
    "./lsp-server-test-apps.log",
    "--app",
]


def create_file(path: str):
    with open(path, "w") as file:
        file.write("")


def lsp_client_server_for(app: str, workspace_path: str):
    root_uri = uri.from_fs_path(str(workspace_path))

    cs_config = ClientServerConfig(
        server_command=SERVER_CMD_BASE + [app],
        root_uri=root_uri,
        client_factory=make_test_client,
    )

    cs = make_client_server(cs_config)
    return cs


def app_test(app: str, initial_file: str, patched_path=None):
    workspace_path = pathlib.Path(__file__).parent / app / "workspace"
    initial_file_path_full = workspace_path / initial_file
    initial_file_uri = uri.from_fs_path(str(initial_file_path_full))

    def wrapper(func):
        @pytest.mark.asyncio
        async def inner(mocker, *args, **kwargs):
            patched = None
            if patched_path is not None:
                patched = mocker.patch(patched_path)
            cs = lsp_client_server_for(app, workspace_path)

            @cs.client.feature(WORKSPACE_APPLY_EDIT)
            def _noop(_):
                return

            await cs.start()
            try:
                create_file(initial_file_path_full)
                cs.client.notify_did_open(initial_file_uri, "", "")
                await func(
                    cs.client, initial_file_uri, *args, **kwargs, patched=patched
                )
            finally:
                # TODO: needs to timeout _before_ pytest-timeout kills this function
                await cs.stop()

        return inner

    return wrapper
