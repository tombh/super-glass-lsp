from typing import Dict, List, Optional, Union
from enum import Enum, auto

from pydantic import BaseModel, Field


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


# TODO: Rename? Because it's specific to diagnostics?
class OutputParsingConfig(BaseModel):
    """Config for the output of CLI tools"""

    @classmethod
    def default(cls):
        return cls(formats=["{item}"])

    formats: List[str] = Field()
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


class LSPFeature(AutoName):
    """All the possible features that a config block can configure"""

    diagnostic = auto()
    completion = auto()
    formatter = auto()


class CLIToolConfigBasic(BaseModel):
    """Absolute minimum config that the LSP server can recieve from the client"""

    enabled: Optional[bool] = Field(True)
    """
    Simply whether this config is used or not.

    Generally all default configs supplied by this project will be disabled. Such that a
    user can enable the config simply by overriding this one field.
    """


class CLIToolConfig(CLIToolConfigBasic):
    """The formal definition of a CLI Tool"""

    lsp_feature: LSPFeature = Field()
    """Specifies which feature of LSP this is configuring"""

    language_id: Optional[str] = Field("*")
    """
    The language to which will trigger this CLI tool behaviour.
    Must be a `language_id` recognised by LSP, eg; `json`, `python`, etc
    """

    command: str = Field()
    """
    The command to run, eg; `"jsonlint --strict"`
    """

    piped: bool = Field(True)
    """
    Whether to pipe the current text document into the command's STDIN
    """

    timeout: int = Field(3)
    """
    How long to let the subprocess run before killing it
    """

    parsing: Optional[OutputParsingConfig] = Field(
        default_factory=OutputParsingConfig.default
    )
    """Config for the output of CLI tools"""


class CLIToolConfigs:
    configs: Dict[str, CLIToolConfig] = Field()
    """
    Parent field for all CLI tool configs.
    This is the entire collection of CLI tools, from linters, formatters, and
    all other manner of strange and wonderful CLI tools.
    """


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    configs: Dict[str, Union[CLIToolConfig, CLIToolConfigBasic]] = Field()
    """
    Parent field for all CLI tool configs.
    This is the entire collection of CLI tools, from linters, formatters, and
    all other manner of strange and wonderful CLI tools.
    """