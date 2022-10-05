from typing import List, Optional

from pydantic import BaseModel, Field


class OutputParsingConfig(BaseModel):
    """Config for the output of CLI tools"""

    format: str = Field(None)
    """
    Token definitions for parsing the output of the CLI tool.
    This a Python token string that defines the components of a parsable line.
    `{msg}`, `{line:d}` and `{col:d}` are required.
    Eg; "{msg} at line {line:d}, column {col:d}"

    See: https://docs.python.org/3/library/string.html#format-specification-mini-language  # noqa
    """

    line_offset: Optional[int] = Field(0)
    """The line index offset if the CLI tool doesn't start at 0, for example"""

    col_offset: Optional[int] = Field(0)
    """The col index offset if the CLI tool doesn't start at 0, for example"""


# TODO: Maybe this should be called DiagnosticCLIToolConfig?
class CLIToolConfig(BaseModel):
    """Configuration options for the server."""

    language_id: str = Field(None)
    """
    The language to which will trigger this CLI tool behaviour.
    Must be a `language_id` recognised by LSP, eg; `json`, `python`, etc
    """

    command: List[str] = Field(None)
    """
    The command to run, eg; `["jsonlint", "--strict"]`
    """

    parsing: OutputParsingConfig = Field(None)
    """Config for the output of CLI tools"""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    clitool_configs: List[CLIToolConfig] = Field()
    """
    Parent field for all CLI tool configs.
    This is the entire collection of CLI tools, from linters, formatters, and
    all other manner of strange and wonderful CLI tools.
    """
