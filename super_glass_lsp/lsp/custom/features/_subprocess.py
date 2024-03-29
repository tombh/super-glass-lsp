from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import os
import asyncio
import psutil  # type: ignore

from super_glass_lsp.lsp.custom.config_definitions import Config


SubprocessArgs = Dict[str, Any]


class SubprocessOutput:
    def __init__(self, stdout: str, stderr: str, returncode: Optional[int]):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def is_non_zero_exit(self) -> bool:
        return self.returncode is None or self.returncode > 0


class Subprocess:
    @classmethod
    async def run(
        cls,
        server: "CustomLanguageServer",
        config: Config,
        command: str,
        input: Optional[str],
        check: bool = True,
    ) -> SubprocessOutput:
        new_env = cls.update_env(config)
        try:
            server.logger.debug(f"Subprocess command: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if input is not None else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=new_env,
            )
            stdout, stderr = await asyncio.wait_for(
                # TODO: Figure out the typing problem here. Is it a false negative?
                process.communicate(input.encode() if input is not None else None),  # type: ignore
                timeout=config.timeout,
            )
            result = SubprocessOutput(
                stdout.decode().strip(), stderr.decode().strip(), process.returncode
            )
            server.logger.debug(f"Subprocess STDOUT: {result.stdout}")
            server.logger.debug(f"Subprocess STDERR: {result.stderr}")
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
            return result
        if process.returncode is None:
            raise Exception("Completed subprocess exited without return code")
        return result

    @classmethod
    def update_env(cls, config: Config) -> Dict:
        new_env = os.environ.copy() | config.env
        if "PYTEST_CURRENT_TEST" in os.environ:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            test_binaries_path = os.path.join(dir_path, "../", "tests", "e2e", "_bin")
            new_env["PATH"] = test_binaries_path + ":" + new_env["PATH"]
        return new_env
