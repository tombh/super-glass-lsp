import pytest  # noqa

from pygls.lsp.types import WorkDoneProgressBegin, ProgressParams

from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit

from ._utils import create_server

MOCK_UUID = 123


# TODO: Put in a integration/ folder
@pytest.mark.asyncio
async def test_disabling(mocker):
    name = "some_work"

    # This mock is needed because of a `transport.write` is None error
    mocker.patch("pygls.protocol.JsonRPCProtocol.send_request")

    notifier = mocker.patch("pygls.protocol.JsonRPCProtocol.notify")
    server, *_ = create_server(
        mocker,
        {
            name: {
                "lsp_feature": "workspace_edit",
                "language_id": "*",
                "command": [
                    "sleep 1",
                    "echo 'TextDocumentEdit /text.txt 0:0,0:0\n🚀'",
                ],
            }
        },
        None,
        "",
    )

    workspace_edit = WorkspaceEdit(server, name)
    workspace_edit.text_doc_uri = "/text.txt"

    await workspace_edit.run_once()
    assert len(notifier.call_args_list) == 0


@pytest.mark.asyncio
async def test_basic_notifications(mocker):
    name = "some_work"

    # This mock is needed because of a `transport.write` is None error
    mocker.patch("pygls.protocol.JsonRPCProtocol.send_request")

    notifier = mocker.patch("pygls.protocol.JsonRPCProtocol.notify")
    server, *_ = create_server(
        mocker,
        {
            name: {
                "lsp_feature": "workspace_edit",
                "language_id": "*",
                "command": ["sleep 1", "echo 'TextDocumentEdit /text.txt 0:0,0:0\n🚀'"],
                "use_lsp_progress": True,
            }
        },
        None,
        "",
    )

    mocker.patch("uuid.uuid4", return_value=MOCK_UUID)

    workspace_edit = WorkspaceEdit(server, name)
    workspace_edit.text_doc_uri = "/text.txt"

    await workspace_edit.run_once()
    assert len(notifier.call_args_list) > 3

    args, _ = notifier.call_args_list[0]
    params = args[1]
    assert params == ProgressParams(
        token=MOCK_UUID,
        value=WorkDoneProgressBegin(
            kind="begin",
            title=f"starting {name}",
            cancellable=None,
            message=None,
            percentage=0,
        ),
    )

    args, _ = notifier.call_args_list[1]
    params = args[1]
    assert params == ProgressParams(
        token=MOCK_UUID,
        value=WorkDoneProgressBegin(
            kind="end",
            title=f"ending {name}",
            cancellable=None,
            message=None,
            percentage=100,
        ),
    )


# TODO: Custom progress reporting behaviour
# @pytest.mark.asyncio
# async def test_custom_config(mocker):
#     name = "some_work"
#
#     # This mock is needed because of a `transport.write` is None error
#     mocker.patch("pygls.protocol.JsonRPCProtocol.send_request")
#
#     notifier = mocker.patch("pygls.protocol.JsonRPCProtocol.notify")
#     server, *_ = create_server(
#         mocker,
#         {
#             name: {
#                 "lsp_feature": "workspace_edit",
#                 "language_id": "*",
#                 "progress": "spinner",
#                 "command": [
#                     "sleep 1",
#                     "echo 'TextDocumentEdit /text.txt 0:0,0:0\n🚀'",
#                 ],
#             },
#             "spinner": {
#                 "lsp_feature": "work_done_progress",
#                 "command": [
#                     "echo 'report 0.5'",
#                     "echo 'doing work'",
#                 ],
#             },
#         },
#         None,
#         "",
#     )
#
#     mocker.patch("uuid.uuid4", return_value=MOCK_UUID)
#
#     workspace_edit = WorkspaceEdit(server, name)
#     workspace_edit.text_doc_uri = "/text.txt"
#
#     await workspace_edit.run_once()
#     assert len(notifier.call_args_list) > 3
#
#     args, _ = notifier.call_args_list[0]
#     params = args[1]
#     assert params == ProgressParams(
#         token=MOCK_UUID,
#         value=WorkDoneProgressBegin(
#             kind='begin',
#             title=f'starting {name}',
#             cancellable=None,
#             message=None,
#             percentage=0
#         )
#     )
#
#     args, _ = notifier.call_args_list[1]
#     params = args[1]
#     assert params == ProgressParams(
#         token=MOCK_UUID,
#         value=WorkDoneProgressBegin(
#             kind='end',
#             title=f'ending {name}',
#             cancellable=None,
#             message=None,
#             percentage=100
#         )
#     )
