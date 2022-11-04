from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import asyncio
import psutil  # type: ignore

from super_glass_lsp.lsp.custom.config_definitions import Config


SubprocessArgs = Dict[str, Any]


class SubprocessOutput:
    def __init__(self, stdout: str, stderr: str):
        self.stdout = stdout
        self.stderr = stderr


class Subprocess:
    @classmethod
    async def run(
        cls,
        server: "CustomLanguageServer",
        config: Config,
        command: str,
        input: Optional[str],
        check: bool = False,
    ) -> SubprocessOutput:
        try:
            server.logger.debug(f"Subprocess command: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                # TODO: Figure out the typing problem here. Is it a false negative?
                process.communicate(input.encode() if input is not None else None),  # type: ignore
                timeout=config.timeout,
            )
            output = SubprocessOutput(stdout.decode(), stderr.decode())
            server.logger.debug(f"Subprocess STDOUT: {output.stdout}")
            server.logger.debug(f"Subprocess STDERR: {output.stderr}")
        except asyncio.TimeoutError:
            message = f"Timeout: `{command}` took longer than {config.timeout} seconds"
            server.logger.warning(message)
            server.show_message(message)
            if process.returncode is None:
                server.logger.warning(
                    f"Terminating subprocess: `{command}` (timed out)"
                )
                parent = psutil.Process(process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
        if process.returncode is None:
            raise Exception("Completed subprocess exited without return code")
        if check and process.returncode > 0:
            message = f"Subprocess error for `{config.command}`: {output.stderr}"
            server.logger.error(message)
            server.show_message(message)
        return output
