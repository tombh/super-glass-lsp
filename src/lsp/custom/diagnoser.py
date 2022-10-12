from typing import List, Optional, TYPE_CHECKING

import logging

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

import subprocess

from parse import parse  # type: ignore
from pygls.lsp.types import (
    Diagnostic,
    Position,
    Range,
)

from .config import CLIToolConfig, OutputParsingConfig


class Diagnoser:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        # TODO: use the name of the CLI tool
        self.name = type(server).__name__

    def run(self, uri: str) -> None:
        if self.server.configuration is None:
            return

        # TODO: only run the CLI tools that match the current language ID
        config = self.server.configuration.clitool_configs[0]

        document = self.server.workspace.get_document(uri)

        if document.language_id != config.language_id:
            return

        diagnostics = self.diagnose(document.source, config)
        self.server.publish_diagnostics(document.uri, diagnostics)

    def build_diagnostic_object(
        self, message: str, line: int = 0, col: int = 0
    ) -> Diagnostic:
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col + 1),
            ),
            message=message,
            source=self.name,
        )

    def parse_line(self, config: OutputParsingConfig, line: str) -> Diagnostic:
        for format_string in config.formats:
            maybe_diagnostic = self.parse_line_maybe(config, format_string, line)
            if maybe_diagnostic is not None:
                return maybe_diagnostic

        # TODO: What's the proper way of communicating this?
        message = "CLI Tool LSP failed to parse CLI output"
        return self.build_diagnostic_object(message)

    def parse_line_maybe(
        self, config: OutputParsingConfig, format_string: str, line: str
    ) -> Optional[Diagnostic]:
        logging.debug(msg=f"Parsing: '{line}' with '{format_string}'")
        parsed = parse(format_string, line)
        if parsed is None:
            return None

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

        logging.debug(msg=f"Parsed `line` as: {line_number}")
        logging.debug(msg=f"Parsed `col` as: {col_number}")
        logging.debug(msg=f"Parsed `msg` as: {message}")

        line_number += line_offset
        col_number += col_offset

        return self.build_diagnostic_object(message, line_number, col_number)

    def run_cli_tool(self, command: List[str], text: str) -> str:
        result = subprocess.run(
            command,
            input=text,
            text=True,
            capture_output=True,
            check=False,
        )

        return result.stderr.strip()

    def diagnose(self, text: str, config: CLIToolConfig) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        output = self.run_cli_tool(config.command, text)
        if not output:
            return diagnostics

        for line in output.splitlines():
            diagnostic = self.parse_line(
                config.parsing,
                line,
            )
            diagnostics.append(diagnostic)

        return diagnostics
