import time
import pytest  # noqa
import pytest_lsp  # noqa

from pytest_lsp.client import Client

from pygls.lsp.types import Diagnostic
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from . import default_config_test


# TODO: all these tests need to have a timeout
@default_config_test("jqlint", "jq", "sample.json")
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

    # First notification is for the "good" version, that there are no errors
    await client.wait_for_notification("textDocument/publishDiagnostics")
    # Second notification is from saving the "bad" version
    await client.wait_for_notification("textDocument/publishDiagnostics")
    # TODO: I think we still need a custom notification that is sent from the server
    # _after_ it has sent the diagnostic. This will guarantee ordering so that we
    # don't need the sleep.
    time.sleep(0.01)

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

    await client.wait_for_notification("textDocument/publishDiagnostics")
    # TODO: see similar note on sleep above
    time.sleep(0.01)

    # Ensure that we remove any resolved diagnostics.
    assert len(client.diagnostics[uri]) == 0
