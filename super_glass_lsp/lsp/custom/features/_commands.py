from typing import Tuple, List

from parse import parse  # type: ignore

from super_glass_lsp.lsp.custom.config_definitions import (
    ShellCommand,
)
from ._subprocess import Subprocess, SubprocessOutput
from ._base import Base
from ._document import Document

Replacements = List[Tuple[str, str]]


class Commands(Document, Base):
    def resolve_commands(self, replacements: Replacements) -> ShellCommand:
        resolved: ShellCommand
        commands = self.command
        if isinstance(commands, list):
            resolved = []
            for command in commands:
                resolved.append(self.replace_tokens(command, replacements))
        else:
            resolved = self.replace_tokens(commands, replacements)

        return resolved

    def replace_tokens(self, string: str, replacements: Replacements) -> str:
        for replacement in replacements:
            string = string.replace(replacement[0], replacement[1])
        return string

    async def run_pre_commands(
        self,
        commands: ShellCommand,
    ):
        format = "call {config_id} {args}"

        if not isinstance(commands, list):
            return

        pre_commands = commands[:-1]

        if len(pre_commands) == 0:
            self.server.logger.warning(
                "Feature.run_pre_commands expected a list of commands but didn't find any"
            )
            return

        for command in pre_commands:
            result = await self.shell(command)
            if result.stdout == "":
                self.server.logger.warning("No output to parse from pre-command")
                continue
            parsed = parse(format, result.stdout)
            if parsed is not None:
                args = parsed["args"].strip()
            else:
                args = ""
                parsed = parse("call {config_id}", result.stdout)
                if parsed is None:
                    raise Exception(f"Couldn't parse output from pre-command: {result}")

            # TODO: at least diagnostic notifications could be supported as pre-commands too
            from super_glass_lsp.lsp.custom.features.workspace_edit import WorkspaceEdit

            workspace_edit = WorkspaceEdit(self.server, parsed["config_id"].strip())
            if self.text_doc_uri is None:
                raise Exception(
                    "WorkspaceEdit called as pre-command must have text_doc_uri"
                )
            workspace_edit.text_doc_uri = self.text_doc_uri
            await workspace_edit.run_once(args)

    async def shell(self, command: str, check: bool = True) -> SubprocessOutput:
        if self.text_doc_uri is not None:
            command = command.replace(
                "{file}", self.text_doc_uri.replace("file://", "")
            )
            command = command.replace("{uri}", self.text_doc_uri)

        if self.server.workspace is not None:
            command = command.replace(
                "{workspace_root}", self.server.workspace.root_path
            )

        input = None
        if self.config.piped and self.text_doc_uri is not None:
            document = self.get_current_document()
            input = document.source
            self.server.logger.debug("Piping the following to STDIN:")
            self.server.logger.debug(input)

        debug = {
            "text_doc_uri": self.text_doc_uri,
            "tool_config": self.config,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        output = await Subprocess.run(self.server, self.config, command, input, check)
        output.stdout = output.stdout.strip()
        output.stderr = output.stderr.strip()
        return output
