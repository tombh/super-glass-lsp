from typing import Dict, List, Optional, Union
from enum import Enum, auto
import os

from pydantic import BaseModel, Field

ShellCommand = Union[str, List[str]]

DEFAULT_FORMATTERS = ["{msg}"]


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


# TODO: Rename? Because it's specific to diagnostics?
class OutputParsingConfig(BaseModel):
    """Config for the output of `command`s run in the sub shell"""

    @classmethod
    def default(cls):
        return cls(formats=DEFAULT_FORMATTERS)

    formats: List[str] = Field()
    """
    Token definitions for parsing the output of the commands.
    This a Python token string that defines the components of a parsable line.
    `{msg}`, `{line:d}` and `{col:d}` are required.
    Eg; "{msg} at line {line:d}, column {col:d}"

    See: https://docs.python.org/3/library/string.html#format-specification-mini-language  # noqa
    """

    line_offset: Optional[int] = Field(0)
    """The line index offset if the CLI tool doesn't 0-index lines, for example"""

    col_offset: Optional[int] = Field(0)
    """The col index offset if the CLI tool doesn't 0-index chars, for example"""


class LSPFeature(AutoName):
    """All the possible features that a config block can configure"""

    diagnostic = auto()
    completion = auto()
    formatter = auto()
    workspace_edit = auto()
    goto_definition = auto()
    work_done_progress = auto()


class ConfigBasic(BaseModel):
    """Absolute minimum config that the LSP server can recieve from the client"""

    # TODO: I do not like this repetition. But we're going to be replacing Pydantic in
    # Pygls v1 anyway, so punting this for another day.
    enabled: bool = Field()
    lsp_feature: Optional[LSPFeature] = Field()
    language_id: Optional[str] = Field()
    root_markers: Optional[List[str]] = Field()
    command: Optional[ShellCommand] = Field()
    use_lsp_progress: Optional[bool] = Field()
    env: Optional[Dict] = Field()
    piped: Optional[bool] = Field()
    stdout: Optional[bool] = Field()
    stderr: Optional[bool] = Field()
    timeout: Optional[int] = Field()
    debounce: Optional[int] = Field()
    parsing: Optional[OutputParsingConfig] = Field()
    period: Optional[int] = Field()

    def has_root_marker(self, root: str) -> bool:
        if self.root_markers is None:
            return True
        for root_marker in self.root_markers:
            path = os.path.join(root, root_marker)
            return os.path.exists(path)
        return False


class Config(ConfigBasic):
    """The formal definition of a single config"""

    enabled: bool = Field(True)
    """
    Simply whether this config is used or not.

    Generally all default configs supplied by this project will be disabled. Such that a
    user can enable the config simply by overriding this one field.
    """

    lsp_feature: LSPFeature = Field()
    """Specifies which feature of LSP this is configuring"""

    language_id: str = Field("*")
    """
    The language that will trigger this config's behaviour.
    Must be a `language_id` recognised by LSP, eg; `json`, `python`, etc
    """

    root_markers: Optional[List[str]] = Field()
    """
    Similar to LSP root markers, in that they express a codnition upon which the server will run.
    For examle the proyect has to contain a `package.json` file in its root.

    This setting is different in that it is local to the server. So it can only enable/disable
    individual configs, not the server itself.
    """

    command: ShellCommand = Field("true")
    """
    The command to run, eg; `"jsonlint --strict"`
    """

    use_lsp_progress: bool = Field(False)
    """
    Use default LSP progress notifications
    """

    # TODO: Custom progress reporting behaviour
    # progress_config: Optional[str] = Field()
    # """
    # Name of config block that provides custom progress reporting behaviour.
    # For example, the ability to use WorkspaceEdit to show a spinner in the editor.
    # """

    env: Dict = Field({})
    """
    Extra environment variables to pass to the shell
    """

    piped: bool = Field(True)
    """
    Whether to pipe the current text document into the command's STDIN
    """

    stdout: Optional[bool] = Field()
    """
    Force checking of output on STDOUT
    """

    stderr: Optional[bool] = Field()
    """
    Force checking of output on STDERR
    """

    timeout: int = Field(3)
    """
    How long to let the subprocess run before killing it
    """

    debounce: int = Field(1000)
    """
    Minimum time in milliseconds between calls to command
    """

    parsing: Optional[OutputParsingConfig] = Field(
        default_factory=OutputParsingConfig.default
    )
    """Config for the output of config commands"""

    period: Optional[int] = Field()
    """
    Automatically call this config from a long-lived daemon, every `period` seconds.
    """


class Configs(BaseModel):
    configs: Dict[str, Config] = Field()
    """
    Parent field for all configs.

    This is the entire collection of CLI tools, from linters, formatters, and
    all other manner of strange and wonderful CLI tools.
    """


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    configs: Dict[str, Union[Config, ConfigBasic]] = Field({})
    """
    Parent field for all configs.

    This is the entire collection of CLI tools, from linters, formatters, and
    all other manner of strange and wonderful CLI tools.
    """
