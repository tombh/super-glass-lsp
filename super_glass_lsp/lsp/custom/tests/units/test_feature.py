import pytest  # noqa

from pygls.lsp.types import Position

from super_glass_lsp.lsp.custom.features._feature import Feature
from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

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


# TODO: Put in a integration/ folder
@pytest.mark.asyncio
async def test_command_failure(mocker):
    notifier = mocker.patch("pygls.protocol.JsonRPCProtocol.notify")

    outputs = [
        SubprocessOutput("", "error", 1),
    ]
    server, _, _ = create_server(
        mocker,
        {
            "config": {
                "lsp_feature": "workspace_edit",
                "language_id": "*",
            }
        },
        outputs,
        "",
    )

    workspace_edit = WorkspaceEdit(server, "config")

    await workspace_edit.run_once()
    assert len(notifier.call_args_list) == 1
    args, _ = notifier.call_args_list[0]
    notification = args[1]
    assert notification.message == "config: error"


# TODO: Put in a integration/ folder
@pytest.mark.asyncio
async def test_pre_commands(mocker):
    send_request = mocker.patch("pygls.protocol.JsonRPCProtocol.send_request")
    server, _, _ = create_server(
        mocker,
        {
            "config": {
                "lsp_feature": "workspace_edit",
                "language_id": "*",
                "command": [
                    "echo 'call other'",
                    "echo 'TextDocumentEdit /text.txt 0:0,0:0\n🚀'",
                ],
            },
            "other": {
                "lsp_feature": "workspace_edit",
                "language_id": "*",
                "command": [
                    "echo 'TextDocumentEdit /text.txt 0:0,0:0\n✨'",
                ],
            },
        },
        None,
        "",
    )

    workspace_edit = WorkspaceEdit(server, "config")
    workspace_edit.text_doc_uri = "/text.txt"

    await workspace_edit.run_once()
    assert len(send_request.call_args_list) == 2
    args, _ = send_request.call_args_list[0]
    params = args[1]
    output = params.edit.document_changes[0].edits[0].new_text
    assert output == "✨"
    args, _ = send_request.call_args_list[1]
    params = args[1]
    output = params.edit.document_changes[0].edits[0].new_text
    assert output == "🚀"
