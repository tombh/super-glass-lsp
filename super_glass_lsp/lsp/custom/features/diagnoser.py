import typing
from typing import TYPE_CHECKING, List, Optional, Dict

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from parse import parse  # type: ignore

from pygls.lsp.types import Diagnostic, Position, Range, DiagnosticSeverity, MessageType

from super_glass_lsp.lsp.custom.config_definitions import (
    OutputParsingConfig,
    LSPFeature,
)
from super_glass_lsp.lsp.custom.features._feature import Feature
from super_glass_lsp.lsp.custom.features._debounce import Debounce


class Diagnoser(Feature):
    @classmethod
    async def run_all(cls, server: "CustomLanguageServer", text_doc_uri: str) -> None:
        configs = Feature.get_configs(server, text_doc_uri, LSPFeature.diagnostic)
        for id, config in configs.items():
            diagnoser = cls(server, id, text_doc_uri)
            if not diagnoser.debouncer.is_debounced():
                await diagnoser.run_one()

    def __init__(
        self, server: "CustomLanguageServer", config_id: str, text_doc_uri: str
    ):
        super().__init__(server, config_id, text_doc_uri)

        Debounce.init(
            self.server,
            config_id,
            self.cache_key(),
            self.run_one,
        )

    async def run_one(self):
        """
        We need to prevent sibling diagnostics tools from clobbering each other
        """
        results = await self.diagnose()
        self.server.diagnostics[self.config_id] = results
        self.server.publish_diagnostics(self.text_doc_uri, self._flatten())

    def _flatten(self) -> List[Diagnostic]:
        flattened: List[Diagnostic] = []
        for _id, diagnostics in self.server.diagnostics.items():
            flattened.extend(diagnostics)
        return flattened

    def build_diagnostic_object(
        self, message: str, line: int = 0, col: int = 0, severity: str = ""
    ) -> Diagnostic:
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col + 1),
            ),
            message=message,
            source=self.name,
            severity=self.match_severity(severity),
        )

    def match_severity(self, severity_string: str) -> DiagnosticSeverity:
        severity_string = severity_string.lower()
        if "error" in severity_string:
            return DiagnosticSeverity.Error
        if "warning" in severity_string:
            return DiagnosticSeverity.Warning
        if "info" in severity_string:
            return DiagnosticSeverity.Information
        if "hint" in severity_string:
            return DiagnosticSeverity.Hint
        if "note" in severity_string:
            return DiagnosticSeverity.Hint
        if severity_string.startswith("e"):
            return DiagnosticSeverity.Error
        if severity_string.startswith("w"):
            return DiagnosticSeverity.Warning
        if severity_string.startswith("i"):
            return DiagnosticSeverity.Information
        return DiagnosticSeverity.Error

    def parse_line(self, line: str) -> Diagnostic:
        if self.config.parsing is not None:
            config = self.config.parsing
        else:
            # TODO: I think we're using 2 different defaults for emptpy formate now?
            config = OutputParsingConfig(**typing.cast(Dict, {"formats": ["{line}"]}))

        for format_string in config.formats:
            maybe_diagnostic = self.parse_line_maybe(
                config, format_string, line
            )  # type: ignore
            if maybe_diagnostic is not None:
                return maybe_diagnostic

        summary = "Super Glass failed to parse shell output"
        command = f"Command: `{self.config.command}`"
        debug = f"{summary}\n{command}\nOutput: {line}"
        self.server.logger.warning(debug)
        self.server.show_message(debug, msg_type=MessageType.Warning)
        # TODO: Maybe not send a diagnostic if there was an error?
        return self.build_diagnostic_object(summary)

    def parse_line_maybe(
        self, parsing: OutputParsingConfig, format_string: str, line: str
    ) -> Optional[Diagnostic]:
        # Most diagnostic tools seem to be 1-indexed. But the LSP spec is zero-indexed
        ZERO_INDEXING = -1

        self.server.logger.debug(msg=f"Parsing: '{line}' with '{format_string}'")
        parsed = parse(format_string, line)
        if parsed is None:
            return None

        severity = "error"
        if format_string.find("{severity}") != -1:
            severity = parsed["severity"]

        line_offset = 0
        if parsing.line_offset is not None:
            line_offset = parsing.line_offset

        col_offset = 0
        if parsing.col_offset is not None:
            col_offset = parsing.col_offset

        line_number = 0
        if format_string.find("{line:d}") != -1:
            line_number = parsed["line"] + line_offset + ZERO_INDEXING

        col_number = 0
        if format_string.find("{col:d}") != -1:
            col_number = parsed["col"] + col_offset + ZERO_INDEXING

        message = parsed["msg"]

        self.server.logger.debug(msg=f"Parsed `line` as: {line_number}")
        self.server.logger.debug(msg=f"Parsed `col` as: {col_number}")
        self.server.logger.debug(msg=f"Parsed `msg` as: {message}")
        self.server.logger.debug(msg=f"Parsed `severity` as: {severity}")

        return self.build_diagnostic_object(message, line_number, col_number, severity)

    async def run_cli_tool(self) -> str:
        output = ""
        result = await self.shell(check=False)

        if self.config.stdout and result.stdout is not None:
            output = result.stdout.strip()

        if not self.config.stdout and result.stderr is not None:
            output = result.stderr.strip()

        return output

    async def diagnose(self) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        output = await self.run_cli_tool()
        if not output:
            return diagnostics

        for line in output.splitlines():
            diagnostic = self.parse_line(line)
            diagnostics.append(diagnostic)
        return diagnostics
