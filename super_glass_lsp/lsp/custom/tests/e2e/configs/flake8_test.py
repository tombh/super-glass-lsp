import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp.types import Diagnostic
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import DiagnosticSeverity

from . import default_config_test, wait_for_diagnostic_count


@default_config_test("flake8", "python", "py")
async def test_flake8(client: Client, file_path: str, uri: str):
    good = """a = 1\n"""

    # Change the file so that it's in the "bad" state, we should see a diagnostic
    # reporting the issue.
    bad = """a ="""
    with open(file_path, "w") as file:
        file.write(bad)

    client.notify_did_change(uri, bad)

    await wait_for_diagnostic_count(client, uri, 1)

    actual = client.diagnostics[uri][0]

    message = "E999 SyntaxError: invalid syntax"
    assert actual == Diagnostic(
        source="flake8",
        message=message,
        range=Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=1),
        ),
        severity=DiagnosticSeverity.Error,
    )

    file = open(file_path, "w")
    file.write(good)

    # Undo the changes, we should see the diagnostic be removed.
    client.notify_did_change(uri, good)

    await wait_for_diagnostic_count(client, uri, 0)

    # Ensure that we remove any resolved diagnostics.
    assert len(client.diagnostics[uri]) == 0
