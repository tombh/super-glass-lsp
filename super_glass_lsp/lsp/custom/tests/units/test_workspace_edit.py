import pytest  # noqa


from pygls.lsp.types import (
    TextEdit,
    TextDocumentEdit,
    TextDocumentIdentifier,
    Position,
    Range,
    ApplyWorkspaceEditParams,
    WorkspaceEdit as WorkspaceEditRequest,
)

from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit
from super_glass_lsp.lsp.custom.features._subprocess import SubprocessOutput

from ._utils import create_server


@pytest.mark.asyncio
async def test_workspace_edit_textedit(mocker):
    send_request = mocker.patch("pygls.protocol.JsonRPCProtocol.send_request")

    new_text = "😊"
    outputs = [
        SubprocessOutput(
            "\n".join(["TextDocumentEdit /text.txt 0:0,0:0", new_text]), "", 0
        ),
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

    changes = TextDocumentEdit(
        text_document=TextDocumentIdentifier(
            uri="file:///text.txt",
        ),
        edits=[
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=0),
                ),
                new_text=new_text,
            )
        ],
    )
    apply_edit = ApplyWorkspaceEditParams(
        edit=WorkspaceEditRequest(document_changes=[changes]),
        label="config document update",
    )
    workspace_edit = WorkspaceEdit(server, "config")

    await workspace_edit.run_once()
    call = send_request.call_args_list[0]
    assert call == call("workspace/applyEdit", apply_edit)
