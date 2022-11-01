import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp.types import Diagnostic
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import DiagnosticSeverity

from . import default_config_test, wait_for_diagnostic_count


@default_config_test("markdownlint", "markdownlint", "md")
async def test_markdownlint(client: Client, file_path: str, uri: str):
    good = """# Markdown Title\n"""

    # Change the file so that it's in the "bad" state, we should see a diagnostic
    # reporting the issue.
    bad = "(bad link)[https://bad.com]"
    with open(file_path, "w") as file:
        file.write(bad)

    client.notify_did_change(uri, bad)

    await wait_for_diagnostic_count(client, uri, 3)

    actual = client.diagnostics[uri][0]

    assert actual == Diagnostic(
        source="markdownlint",
        message="MD011/no-reversed-links Reversed link syntax [(bad link)[https://bad.com]]",
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
