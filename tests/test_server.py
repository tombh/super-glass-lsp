import pytest  # noqa

from src.lsp.definition import CLIToolsLanguageServer


def test_server_instantiates():
    server = CLIToolsLanguageServer()
    assert server
