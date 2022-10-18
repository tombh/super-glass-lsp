import time
import pytest  # noqa
import pytest_lsp  # noqa

from pytest_lsp.client import Client

from pygls.lsp.types import Diagnostic
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from . import config_test_needs


@config_test_needs("jqlint", "jq", "sample.json")
async def test_jq_linter(client: Client, file_path: str, uri: str):
    file = open(file_path, "r")
    good = file.read()

    # Change the file so that it's in the "bad" state, we should see a diagnostic
    # reporting the issue.
    bad = "{,}"
    file = open(file_path, "w")
    file.write(bad)

    client.notify_did_change(uri, bad)
    client.notify_did_save(uri, bad)

    # TODO: Why do we have to wait? Isn't the notification enough
    # Maybe there are better notifications to wait for? Even make our own one?
    # await client.wait_for_notification("textDocument/publishDiagnostics")
    time.sleep(1)

    actual = client.diagnostics[uri][0]

    assert actual == Diagnostic(
        source="CustomLanguageServer",
        message="parse error: Expected value before ','",
        range=Range(
            start=Position(line=1, character=2),
            end=Position(line=1, character=3),
        ),
    )

    file = open(file_path, "w")
    file.write(good)

    # Undo the changes, we should see the diagnostic be removed.
    client.notify_did_change(uri, good)
    client.notify_did_save(uri, good)

    time.sleep(1)

    # Ensure that we remove any resolved diagnostics.
    assert len(client.diagnostics[uri]) == 0
