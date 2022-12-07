import pytest  # noqa
import pytest_lsp  # noqa


from pytest_lsp.client import Client

from pygls.lsp.types import CompletionList

from . import default_config_test


# TODO: might be good to check for `tr`, `cat`, `uniq`, etc?
@default_config_test("fuzzy_buffer_tokens", "fzf", "md")
async def test_fzf_buffer(client: Client, file_path: str, uri: str):
    contents = "foo far bar f"
    client.notify_did_change(uri, contents)

    line = 0
    character = len(contents) + 1

    response = await client.completion_request(uri, line, character)

    assert isinstance(response, CompletionList)

    assert len(response.items) == 3
    labels = [item.label for item in response.items]
    assert "f" in labels
    assert "far" in labels
    assert "foo" in labels
