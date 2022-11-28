import typing
from typing import Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import os
import asyncio

from parse import parse  # type: ignore

from pygls.lsp.types import (
    WorkspaceEdit as WorkspaceEditRequest,
    TextDocumentContentChangeEvent,
    TextDocumentEdit,
    TextDocumentIdentifier,
    MessageType,
    TextEdit,
)

from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    OutputParsingConfig,
)
from super_glass_lsp.lsp.custom.features._feature import Feature


class WorkspaceEdit(Feature):
    @classmethod
    def start_all_daemons(
        cls,
        server: "CustomLanguageServer",
    ):
        # TODO: think about how language IDs fit into Workspace Edits
        language_id = "*"
        configs = server.custom.get_all_config_by(
            LSPFeature.workspace_edit, language_id, allow_missing_root_marker=True
        )
        for id, config in configs.items():
            if config.period is not None:
                instance = cls(server, id)
                server.loop.create_task(instance.start_daemon())

    async def start_daemon(self):
        self.server.logger.info(f"Starting WorkspaceEdit daemon: {self.config_id}")
        if self.config.period is None:
            raise Exception

        while True:
            await self.run_once()
            if "PYTEST_CURRENT_TEST" in os.environ:
                break
            await asyncio.sleep(float(self.config.period))

    def __init__(self, server: "CustomLanguageServer", config_id: str):
        text_doc_uri = None  # TODO: think about what text_doc_uri means in this feature
        super().__init__(server, config_id, text_doc_uri)

    async def run_once(
        self,
    ):
        if not self.config.has_root_marker(self.server.custom.get_workspace_root()):
            return
        result = await self.shell()
        output = result.stdout.strip()
        workspace_edit = self.build_workspace_edit(output)
        self.send_workspace_edit(workspace_edit)

    def send_workspace_edit(self, workspace_edit: WorkspaceEditRequest):
        self.server.logger.debug("Sending Workspace Edit")
        self.server.lsp.apply_edit(workspace_edit, f"{self.config_id} document update")

        # TODO: I think this is a bug in Pygls that we're fixing?
        edit = workspace_edit.document_changes[0].edits[0]  # type: ignore
        change = TextDocumentContentChangeEvent(range=edit.range, text=edit.new_text)
        self.get_current_document().apply_change(change)

    # TODO: Refactor with what Diagnoser is also doing
    def build_workspace_edit(self, output: str) -> Optional[WorkspaceEditRequest]:
        default_format = (
            "{kind} {uri} {start_line}:{start_char},{end_line}:{end_char}\n{text_edit}"
        )

        if (
            self.config.parsing is not None
            and self.config.parsing != OutputParsingConfig.default()
        ):
            config = self.config.parsing
        else:
            config = OutputParsingConfig(
                **typing.cast(Dict, {"formats": [default_format]})
            )

        for format_string in config.formats:
            maybe_workspace_edit = self.parse_output(
                config, format_string, output
            )  # type: ignore
            if maybe_workspace_edit is not None:
                return maybe_workspace_edit

        summary = "Super Glass failed to parse shell output"
        command = f"Command: `{self.config.command}`"
        debug = f"{summary}\n{command}\nOutput: {output}"
        self.server.logger.warning(debug)
        self.server.show_message(debug, msg_type=MessageType.Warning)
        return None

    # `kind`: TextDocumentEdit | CreateFile | RenameFile | DeleteFile
    # `uri`: Text document URI
    # `range` (only for TextDocumentEdit): start_line,start_char,end_line,end_char
    # `text_edit`: All remaining lines
    # TODO: perhaps this could be made a default formatter?
    def parse_output(
        self, parsing: OutputParsingConfig, format_string: str, output: str
    ) -> Optional[WorkspaceEditRequest]:
        self.server.logger.debug(msg=f"Parsing: '{output}' with '{format_string}'")
        parsed = parse(format_string, output)
        if parsed is None:
            return None

        uri = f"file://{parsed['uri']}"
        self.text_doc_uri = uri

        # TODO: if parsed["kind"] == "TextDocumentEdit" ...

        edit = TextDocumentEdit(
            text_document=TextDocumentIdentifier(
                uri=uri,
            ),
            edits=[
                TextEdit(
                    range=self.parse_range(
                        parsed["start_line"],
                        parsed["start_char"],
                        parsed["end_line"],
                        parsed["end_char"],
                    ),
                    new_text=parsed["text_edit"],
                ),
            ],
        )
        # Also CreateFile, RenameFile, DeleteFile can go in the list
        return WorkspaceEditRequest(document_changes=[edit])
