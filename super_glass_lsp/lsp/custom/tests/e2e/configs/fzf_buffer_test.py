import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp.types import CompletionList

from . import default_config_test


# TODO: might be good to check for `tr`, `cat`, `uniq`, etc?
@default_config_test("fuzzy_buffer_tokens", "fzf", "md")
async def test_fzf_buffer(client: Client, file_path: str, uri: str):
    contents = "foo bar f"
    client.notify_did_change(uri, contents)

    line = 0
    character = 9  # TODO: automatically calculate last char from `contents` var?

    response = await client.completion_request(uri, line, character)

    assert isinstance(response, CompletionList)

    assert len(response.items) == 2
    assert response.items[0].label == "f"
    assert response.items[1].label == "foo"
