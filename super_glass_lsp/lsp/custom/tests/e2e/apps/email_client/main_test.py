import pytest  # noqa
import pytest_lsp  # noqa

from super_glass_lsp.lsp.custom.tests.e2e.apps._utils import app_test
from pytest_lsp.client import Client


@app_test("email_client", "inbox.md")
async def test_inbox_loads(client: Client, uri: str):
    # wait for inbox.md to load
    assert True
