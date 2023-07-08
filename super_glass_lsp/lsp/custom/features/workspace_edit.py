from typing import Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import os
import asyncio

from parse import parse  # type: ignore

from pygls.lsp.types import (
    WorkspaceEdit as WorkspaceEditRequest,
    TextDocumentEdit,
    DeleteFile,
    TextDocumentIdentifier,
    TextEdit,
)

from ._feature import Feature
from ._commands import Commands
from super_glass_lsp.lsp.custom.config_definitions import (
    LSPFeature,
    OutputParsingConfig,
)

# `kind`: TextDocumentEdit | CreateFile | RenameFile | DeleteFile
# `uri`: Text document URI
# `range` (only for TextDocumentEdit): start_line,start_char,end_line,end_char
# `text_edit`: All remaining lines
DEFAULT_FORMATTERS = [
    "{kind} {uri} {start_line}:{start_char},{end_line}:{end_char}\n{text_edit}",
    "{kind} {uri} {start_line}:{start_char},{end_line}:{end_char}",
    "{kind} {uri}",
]


class WorkspaceEdit(Feature, Commands):
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
        super().__init__(server, config_id, None)

    async def run_once(self, args: Optional[str] = None) -> bool:
        if not self.config.has_root_marker(self.server.custom.get_workspace_root()):
            return True

        replacements = []
        if args:
            replacements = [
                ("{args}", args),
            ]
        commands = self.resolve_commands(replacements)
        is_success = await self.run_pre_commands(commands)
        if not is_success:
            return False

        if isinstance(commands, list):
            final_command = commands[-1]
        else:
            final_command = commands
        result = await self.shell(final_command)
        if result.is_non_zero_exit():
            return False

        workspace_edit = self.build_workspace_edit(result.stdout)
        if workspace_edit is not None:
            self.send_workspace_edit(workspace_edit)

        return True

    def send_workspace_edit(self, workspace_edit: WorkspaceEditRequest):
        self.server.logger.debug("Sending Workspace Edit")
        self.server.lsp.apply_edit(workspace_edit, f"{self.config_id} document update")

    def build_workspace_edit(self, output: str) -> Optional[WorkspaceEditRequest]:
        config = self.get_parsing_config(DEFAULT_FORMATTERS)
        for format_string in config.formats:
            maybe_workspace_edit = self.parse_output(
                config, format_string, output
            )  # type: ignore
            if maybe_workspace_edit is not None:
                return maybe_workspace_edit

        self.parsing_failed(output)
        return None

    def parse_output(
        self, parsing: OutputParsingConfig, format_string: str, output: str
    ) -> Optional[WorkspaceEditRequest]:
        self.server.logger.debug(msg=f"Parsing: '{output}' with '{format_string}'")
        parsed = parse(format_string, output)
        if parsed is None:
            return None

        uri = f"file://{parsed['uri']}"
        self.text_doc_uri = uri

        edit: Union[None, TextDocumentEdit, DeleteFile] = None

        if parsed["kind"] == "TextDocumentEdit":
            new_text = parsed["text_edit"].replace("\\n", "\n")
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
                        new_text=new_text,
                    ),
                ],
            )

        if parsed["kind"] == "DeleteFile":
            edit = DeleteFile(
                uri=uri,
            )

        # TODO: Also CreateFile, RenameFile

        return WorkspaceEditRequest(document_changes=[edit])
