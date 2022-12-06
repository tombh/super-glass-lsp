import pytest  # noqa

from pygls.lsp.types import Position

from super_glass_lsp.lsp.custom.features._feature import Feature

from ._utils import create_server


@pytest.mark.skip(reason="This is what my Neovim expects, does neovim have a bug?")
@pytest.mark.asyncio
async def test_finding_wordish_under_cursor(mocker):
    config_id = "config"
    server, uri, subprocess_mock = create_server(
        mocker,
        {
            config_id: {
                "lsp_feature": "workspace_edit",
            },
        },
        [],
        "1 | foo | 📥 | ✨ | 🚢",
    )

    feature = Feature(server, config_id, uri)

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=0))
    assert wordish == "1"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=5))
    assert wordish == "foo"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=10))
    assert wordish == "📥"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=12))
    assert wordish == "📥"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=15))
    assert wordish == "✨"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=16))
    assert wordish == "✨"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=19))
    assert wordish == "🚢"

    wordish = feature.get_wordish_under_cursor(Position(line=0, character=21))
    assert wordish == "🚢"
