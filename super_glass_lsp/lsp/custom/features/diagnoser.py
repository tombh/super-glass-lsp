import typing
from typing import List, Optional, Dict, Union

from parse import parse  # type: ignore
from pygls.lsp.types import Diagnostic, Position, Range, DiagnosticSeverity, MessageType

from super_glass_lsp.lsp.custom.config_definitions import (
    Config,
    OutputParsingConfig,
    LSPFeature,
)
from super_glass_lsp.lsp.custom.features import Feature, Debounced


class Diagnoser(Feature):
    async def run(self, text_doc_uri: str) -> None:
        if self.server.configuration is None:
            return

        document = self.get_document_from_uri(text_doc_uri)

        configs = self.server.custom.get_all_config_by(
            LSPFeature.diagnostic, document.language_id
        )
        for id, config in configs.items():
            self.config_id = id
            self.config = config
            if document.language_id == config.language_id:
                diagnostics = await self.diagnose(text_doc_uri, config)
                if not isinstance(diagnostics, Debounced):
                    self.server.publish_diagnostics(document.uri, diagnostics)

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

    def parse_line(
        self, maybe_config: Optional[OutputParsingConfig], line: str, command: str
    ) -> Diagnostic:
        if maybe_config is not None:
            config = maybe_config
        else:
            config = OutputParsingConfig(**typing.cast(Dict, {"formats": ["{line}"]}))

        for format_string in config.formats:
            maybe_diagnostic = self.parse_line_maybe(
                config, format_string, line
            )  # type: ignore
            if maybe_diagnostic is not None:
                return maybe_diagnostic

        summary = "Super Glass failed to parse shell output"
        command = f"Command: `{command}`"
        debug = f"{summary}\n{command}\nOutput: {line}"
        self.server.logger.warning(debug)
        self.server.show_message(debug, msg_type=MessageType.Warning)
        # TODO: Maybe not send a diagnostic if there was an error?
        return self.build_diagnostic_object(summary)

    def parse_line_maybe(
        self, config: OutputParsingConfig, format_string: str, line: str
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
        if config.line_offset is not None:
            line_offset = config.line_offset

        col_offset = 0
        if config.col_offset is not None:
            col_offset = config.col_offset

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

    async def run_cli_tool(
        self, command: str, text_doc_uri: str, use_stdout: Optional[bool] = False
    ) -> Union[str, Debounced]:
        output = ""
        result = await self.shell(command, text_doc_uri, check=False)

        if not isinstance(result, Debounced):
            if use_stdout and result.stdout is not None:
                output = result.stdout.strip()

            if not use_stdout and result.stderr is not None:
                output = result.stderr.strip()

        return output

    async def diagnose(
        self, text_doc_uri: str, config: Config
    ) -> Union[List[Diagnostic], Debounced]:
        diagnostics: List[Diagnostic] = []

        output = await self.run_cli_tool(config.command, text_doc_uri, config.stdout)

        if isinstance(output, Debounced):
            return output

        if not output:
            return diagnostics

        for line in output.splitlines():
            diagnostic = self.parse_line(config.parsing, line, config.command)
            diagnostics.append(diagnostic)

        return diagnostics
