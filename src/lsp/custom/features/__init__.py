from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from src.lsp.server import CustomLanguageServer

import subprocess

from src.lsp.custom.config_definitions import CLIToolConfig

SubprocessArgs = Dict[str, Any]


class Feature:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        # TODO: Use the config ID of the currently active feature?
        self.name = type(server).__name__

        # TODO: Don't make this optional. Maybe it should be the config ID, then look up the
        # actual config on self.server?
        self.config: Optional[CLIToolConfig] = None

    def shell(
        self,
        command: str,
        text_doc_uri: Optional[str] = None,
        extra_subprocess_args: SubprocessArgs = {},
    ):
        if self.config is None:
            raise Exception

        subprocess_args: SubprocessArgs = {
            "timeout": self.config.timeout,
            # Pipe to STDIN
            "text": True,
        }
        subprocess_args = {**subprocess_args, **extra_subprocess_args}

        if self.config is not None and self.config.piped and text_doc_uri is not None:
            document = self.server.workspace.get_document(text_doc_uri)
            subprocess_args["input"] = document.source

        try:
            result = subprocess.run(["sh", "-c", command], **subprocess_args)
        except subprocess.TimeoutExpired:
            message = (
                f"Timeout: `{command}` took longer than {self.config.timeout} seconds"
            )
            self.server.logger.warning(message)
            self.server.show_message(message)
            result = subprocess.CompletedProcess("", returncode=1)
        return result
