import pytest  # noqa
import shutil
import sys
import pathlib
import asyncio

import pygls.uris as uri
from pytest_lsp.client import Client
from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client

from super_glass_lsp.lsp.custom.hub import Hub

ROOT_PATH = pathlib.Path(__file__).parent / "workspace"
SERVER_CMD = [
    "timeout",
    "30",
    sys.executable,
    "super_glass_lsp/main.py",
    "--logfile",
    "./lsp-server-test.log",
]


@pytest.fixture(autouse=True)
def run_around_tests():
    yield


def lsp_client_server_for(id: str):
    root_uri = uri.from_fs_path(str(ROOT_PATH))

    cs_config = ClientServerConfig(
        server_command=SERVER_CMD,
        root_uri=root_uri,
        initialization_options={
            "configs": {
                id: {
                    "enabled": True,
                    "debounce": 0,
                }
            }
        },
        client_factory=make_test_client,
    )

    cs = make_client_server(cs_config)
    return cs


def create_file(path: str):
    with open(path, "w") as file:
        file.write("")


# TODO: handle multiple executbales?
def default_config_test(id: str, executable: str, extension: str):
    """
    All the setup needed to test configs.
      * Starting/stopping a dedicated server in the background.
      * Checking for the external executbales the config depends on.
      * Creating the file that the LSP server works with.
    """

    sample_file_path = f"{id}.{extension}"

    def wrapper(func):
        reason = f"`{executable}` executable not found"

        @pytest.mark.skipif(not shutil.which(executable), reason=reason)
        @pytest.mark.asyncio
        async def inner(*args, **kwargs):
            cs = lsp_client_server_for(id)
            await cs.start()
            try:
                sample_file_path_full = ROOT_PATH / sample_file_path
                sample_uri = uri.from_fs_path(str(sample_file_path_full))
                create_file(sample_file_path_full)
                sample_file = open(sample_file_path_full)
                config = Hub.load_default_config()
                if "enabled" not in config["configs"][id] or not config["configs"][id]:
                    raise Exception(
                        f"Found a default config that isn't disabled: {id}.\n"
                        "Probably just need to add `<<: *defaults`."
                    )
                language_id = config["configs"][id]["language_id"]
                cs.client.notify_did_open(sample_uri, language_id, sample_file.read())

                await func(
                    cs.client, sample_file_path_full, sample_uri, *args, **kwargs
                )
            finally:
                # TODO: needs to timeout _before_ pytest-timeout kills this function
                await cs.stop()

        return inner

    return wrapper


async def wait_for_diagnostic_count(
    client: Client, uri: str, count: int, timeout: int = 4
):
    pause = 0.01
    accumulated = 0.0
    while True:
        accumulated += pause
        if accumulated > timeout:
            actual = 0
            if client.diagnostics.get(uri) is not None:
                actual = len(client.diagnostics[uri])
            raise Exception(
                f"Diagnostic count ({actual}) didn't reach target "
                + f"of {count} in timeout of {timeout}."
            )
        await asyncio.sleep(pause)

        if client.diagnostics.get(uri) is None:
            continue
        elif len(client.diagnostics[uri]) != count:
            continue
        elif len(client.diagnostics[uri]) == count:
            return
