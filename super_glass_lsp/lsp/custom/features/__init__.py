from typing import TYPE_CHECKING, Optional, Dict, Any, Union

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import time
import subprocess

from super_glass_lsp.lsp.custom.config_definitions import Config

SubprocessArgs = Dict[str, Any]


class Debounced:
    pass


class Feature:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        self.config_id: Optional[str] = None
        self.config: Optional[Config] = None

        self.cache: Dict[str, Any] = {}
        """Cache"""

        self.debounces: Dict[str, int] = {}
        """
        Storage for debounce timeouts
        """

    @property
    def name(self):
        return self.config_id

    def get_document_from_uri(self, uri: str):
        return self.server.workspace.get_document(uri)

    def _build_cache_key(self, text_doc_uri: str):
        if self.config_id is None:
            raise Exception(
                "Feature.cache: could not build cache key with None `config_id`"
            )
        return f"{self.config_id}__{text_doc_uri}"

    def set_cache(self, text_doc_uri: str, items: Any):
        key = self._build_cache_key(text_doc_uri)
        self.cache[key] = items

    def get_cache(self, text_doc_uri: str) -> Any:
        key = self._build_cache_key(text_doc_uri)
        return self.cache[key]

    def shell(
        self,
        command: str,
        text_doc_uri: str,
        extra_subprocess_args: SubprocessArgs = {},
    ) -> Union[subprocess.CompletedProcess, Debounced]:
        if self.config_id is None or self.config is None:
            raise Exception

        if self.debounce(text_doc_uri):
            return Debounced()

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
            document = self.get_document_from_uri(text_doc_uri)
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
        except subprocess.CalledProcessError as error:
            message = f"Shell error for `{command}`: {error.stderr}"
            self.server.logger.error(message)
            self.server.show_message(message)
            result = subprocess.CompletedProcess("", returncode=1)
        return result

    def milliseconds_now(self):
        return time.time() * 1000

    # TODO: this feels like it could be its own class
    def debounce(self, text_doc_uri: str):
        if self.config_id is None or self.config is None:
            raise Exception

        key = self._build_cache_key(text_doc_uri)

        if key not in self.debounces:
            self._reset_debounce(key)
            return False

        elapsed = self.milliseconds_now() - self.debounces[key]
        if elapsed > self.config.debounce:
            self._reset_debounce(key)
            return False

        self.server.logger.debug(f"Debouncing: {self.config_id} ({elapsed}ms)")
        return True

    def _reset_debounce(self, key: str):
        self.debounces[key] = self.milliseconds_now()
