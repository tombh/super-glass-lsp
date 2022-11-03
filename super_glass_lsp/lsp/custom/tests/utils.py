from typing import List

from pygls.lsp.types import Diagnostic, DiagnosticSeverity, Range, Position


def make_diagnostic(position: List[int], message: str, source: str):
    return Diagnostic(
        range=Range(
            start=Position(line=position[0], character=position[1]),
            end=Position(line=position[2], character=position[3]),
        ),
        message=message,
        source=source,
        severity=DiagnosticSeverity.Error,
    )
