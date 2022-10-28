import typing
from typing import List, Optional, Dict

from parse import parse  # type: ignore
from pygls.lsp.types import Diagnostic, Position, Range, DiagnosticSeverity

from super_glass_lsp.lsp.custom.config_definitions import (
    Config,
    OutputParsingConfig,
    LSPFeature,
)
from super_glass_lsp.lsp.custom.features import Feature


class Diagnoser(Feature):
    # TODO: test as e2e
    def run(self, text_doc_uri: str) -> None:
        if self.server.configuration is None:
            return

        document = self.server.workspace.get_document(text_doc_uri)

        configs = self.server.custom.get_all_config_by(
            LSPFeature.diagnostic, document.language_id
        )
        for _id, config in configs.items():
            self.config = config
            if document.language_id == config.language_id:
                diagnostics = self.diagnose(text_doc_uri, config)
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
        self, maybe_config: Optional[OutputParsingConfig], line: str
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

        # TODO: What's the proper way of communicating this?
        message = "Super Glaass failed to parse shell output"
        self.server.logger.warning(f"{message}: {line}")
        return self.build_diagnostic_object(message)

    def parse_line_maybe(
        self, config: OutputParsingConfig, format_string: str, line: str
    ) -> Optional[Diagnostic]:
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
            line_number = parsed["line"]

        col_number = 0
        if format_string.find("{col:d}") != -1:
            col_number = parsed["col"]

        message = parsed["msg"]

        self.server.logger.debug(msg=f"Parsed `line` as: {line_number}")
        self.server.logger.debug(msg=f"Parsed `col` as: {col_number}")
        self.server.logger.debug(msg=f"Parsed `msg` as: {message}")
        self.server.logger.debug(msg=f"Parsed `severity` as: {severity}")

        line_number += line_offset
        col_number += col_offset

        return self.build_diagnostic_object(message, line_number, col_number, severity)

    def run_cli_tool(
        self, command: str, text_doc_uri: str, use_stdout: Optional[bool] = False
    ) -> str:
        output = ""
        extra_args = {
            # Rather confusingly, some linters successfully show their diagnostics but exit
            # with a non-zero exit code.
            # TODO: Grep for at least "command not found"
            "check": False,
        }
        result = self.shell(command, text_doc_uri, extra_args)

        if use_stdout and result.stdout is not None:
            output = result.stdout.strip()

        if not use_stdout and result.stderr is not None:
            output = result.stderr.strip()

        return output

    def diagnose(self, text_doc_uri: str, config: Config) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        output = self.run_cli_tool(config.command, text_doc_uri, config.stdout)
        if not output:
            return diagnostics

        for line in output.splitlines():
            diagnostic = self.parse_line(
                config.parsing,
                line,
            )
            diagnostics.append(diagnostic)

        return diagnostics
