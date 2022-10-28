from typing import TYPE_CHECKING, Optional, Dict, Any

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import subprocess

from super_glass_lsp.lsp.custom.config_definitions import Config

SubprocessArgs = Dict[str, Any]


class Feature:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        # TODO: Use the config ID of the currently active feature?
        self.name = type(server).__name__

        # TODO: Don't make this optional. Maybe it should be the config ID, then look up the
        # actual config on self.server?
        self.config: Optional[Config] = None

    def shell(
        self,
        command: str,
        text_doc_uri: Optional[str] = None,
        extra_subprocess_args: SubprocessArgs = {},
    ):
        if self.config is None:
            raise Exception

        if text_doc_uri is not None:
            command = command.replace("{file}", text_doc_uri.replace("file://", ""))

        subprocess_args: SubprocessArgs = {
            "timeout": self.config.timeout,
            "check": True,
            "capture_output": True,
            "text": True,
        }
        subprocess_args = {**subprocess_args, **extra_subprocess_args}

        if self.config is not None and self.config.piped and text_doc_uri is not None:
            document = self.server.workspace.get_document(text_doc_uri)
            subprocess_args["input"] = document.source

        debug = {
            "text_doc_uri": text_doc_uri,
            "tool_config": self.config,
            "shell_config": subprocess_args,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        try:
            self.server.logger.debug(f"subprocess.run() command: {command}")
            result = subprocess.run(["sh", "-c", command], **subprocess_args)
            self.server.logger.debug(f"subprocess.run() STDOUT: {result.stdout}")
            self.server.logger.debug(f"subprocess.run() STDERR: {result.stderr}")
        except subprocess.TimeoutExpired:
            message = (
                f"Timeout: `{command}` took longer than {self.config.timeout} seconds"
            )
            self.server.logger.warning(message)
            self.server.show_message(message)
            result = subprocess.CompletedProcess("", returncode=1)
        except subprocess.CalledProcessError:
            message = f"Shell error for `{command}`: {result.stdout}"
            self.server.logger.error(message)
            self.server.show_message(message)
        return result
