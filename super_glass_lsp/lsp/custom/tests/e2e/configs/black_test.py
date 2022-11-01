import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp import (
    DocumentFormattingParams,
    TextDocumentIdentifier,
)
from pygls.lsp.methods import (
    FORMATTING,
)
from pygls.lsp.types import FormattingOptions

from . import default_config_test

holy_2_space_indent_client = FormattingOptions(
    tab_size=2,
    insert_spaces=True,
)


@default_config_test("black", "black", "py")
async def test_black(client: Client, file_path: str, uri: str):
    contents = "\n".join(
        ['foo1={"bar1":True}', 'foo2={"bar2":"🫠"}', 'foo3={"bar3":False}']
    )
    client.notify_did_change(uri, contents)

    response = client.lsp.send_request(
        FORMATTING,
        DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri=uri),
            options=holy_2_space_indent_client,
        ),
    ).result()

    assert len(response) == 1
    assert response[0] == {
        "newText": 'foo1 = {"bar1": True}\nfoo2 = {"bar2": "🫠"}\nfoo3 = {"bar3": False}',
        "range": {
            "start": {"character": 0, "line": 0},
            "end": {"character": 0, "line": 3},
        },
    }
