from typing import TYPE_CHECKING, Optional, Dict, Any, Union

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import time
import asyncio
import psutil  # type: ignore

from super_glass_lsp.lsp.custom.config_definitions import Config

SubprocessArgs = Dict[str, Any]


class SubprocessOutput:
    def __init__(self, stdout: str, stderr: str):
        self.stdout = stdout
        self.stderr = stderr


class Debounced:
    pass


class Feature:
    def __init__(self, server: "CustomLanguageServer"):
        self.server = server

        self.config_id: Optional[str] = None
        self.config: Optional[Config] = None

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
        self.server.cache[key] = items

    def get_cache(self, text_doc_uri: str) -> Any:
        key = self._build_cache_key(text_doc_uri)
        return self.server.cache[key]

    async def shell(
        self,
        command: str,
        text_doc_uri: str,
        check: bool = True,
    ) -> Union[SubprocessOutput, Debounced]:
        if self.config_id is None or self.config is None:
            raise Exception

        if self.debounce(text_doc_uri):
            return Debounced()

        if text_doc_uri is not None:
            command = command.replace("{file}", text_doc_uri.replace("file://", ""))

        input = None
        if self.config is not None and self.config.piped and text_doc_uri is not None:
            document = self.get_document_from_uri(text_doc_uri)
            input = document.source

        debug = {
            "text_doc_uri": text_doc_uri,
            "tool_config": self.config,
        }
        self.server.logger.debug(f"subprocess.run() config: {debug}")

        output = await self._subprocess_run(command, input, check)
        return output

    async def _subprocess_run(
        self, command: str, input: Optional[str], check: bool = False
    ) -> SubprocessOutput:
        if self.config_id is None or self.config is None:
            raise Exception
        try:
            self.server.logger.debug(f"Subprocess command: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                # TODO: Figure out the typing problem here. Is it a false negative?
                process.communicate(input.encode() if input is not None else None),  # type: ignore
                timeout=self.config.timeout,
            )
            output = SubprocessOutput(stdout.decode(), stderr.decode())
            self.server.logger.debug(f"Subprocess STDOUT: {output.stdout}")
            self.server.logger.debug(f"Subprocess STDERR: {output.stderr}")
        except asyncio.TimeoutError:
            message = (
                f"Timeout: `{command}` took longer than {self.config.timeout} seconds"
            )
            self.server.logger.warning(message)
            self.server.show_message(message)
            if process.returncode is None:
                self.server.logger.warning(
                    f"Terminating subprocess: `{command}` (timed out)"
                )
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
        if process.returncode is None:
            raise Exception("Completed subprocess exited without return code")
        if check and process.returncode > 0:
            message = f"Subprocess error for `{command}`: {output.stderr}"
            self.server.logger.error(message)
            self.server.show_message(message)
        return output

    def milliseconds_now(self):
        return time.time() * 1000

    # TODO: this feels like it could be its own class
    def debounce(self, text_doc_uri: str):
        if self.config_id is None or self.config is None:
            raise Exception

        key = self._build_cache_key(text_doc_uri)

        if key not in self.server.debounces:
            self._reset_debounce(key)
            return False

        elapsed = self.milliseconds_now() - self.server.debounces[key]
        if elapsed > self.config.debounce:
            self._reset_debounce(key)
            return False

        self.server.logger.debug(f"Debouncing: {self.config_id} ({elapsed}ms)")
        return True

    def _reset_debounce(self, key: str):
        self.server.debounces[key] = self.milliseconds_now()
