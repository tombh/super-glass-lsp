import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp.types import Diagnostic
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import DiagnosticSeverity

from . import default_config_test, wait_for_diagnostic_count

TIMEOUT = 16


@pytest.mark.timeout(TIMEOUT)
@default_config_test("mypy", "python", "py")
async def test_mypy(client: Client, file_path: str, uri: str):
    good = """a: int = 1"""

    # Change the file so that it's in the "bad" state, we should see a diagnostic
    # reporting the issue.
    bad = """a: int = 1\na = ''"""
    with open(file_path, "w") as file:
        file.write(bad)

    client.notify_did_change(uri, bad)

    await wait_for_diagnostic_count(client, uri, 1, timeout=TIMEOUT - 1)

    actual = client.diagnostics[uri][0]

    message = (
        "Incompatible types in assignment (expression has "
        'type "str", variable has type "int")'
    )
    assert actual == Diagnostic(
        source="mypy",
        message=message,
        range=Range(
            start=Position(line=1, character=0),
            end=Position(line=1, character=1),
        ),
        severity=DiagnosticSeverity.Error,
    )

    file = open(file_path, "w")
    file.write(good)

    # Undo the changes, we should see the diagnostic be removed.
    client.notify_did_change(uri, good)

    await wait_for_diagnostic_count(client, uri, 0, timeout=TIMEOUT - 1)

    # Ensure that we remove any resolved diagnostics.
    assert len(client.diagnostics[uri]) == 0
