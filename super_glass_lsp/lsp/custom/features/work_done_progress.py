from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import uuid

from pygls.lsp.types import WorkDoneProgressBegin

from ._feature import Feature

# TODO: Custom progress behaviour
# # `kind`: begin | report | end
# # `percentage`: Floating point indicator of progress
# # `message`: All remaining lines
# DEFAULT_FORMATTERS = [
#     "{kind} {percentage}\n{text_edit}",
#     "{kind} {percentage}",
#     "{kind}",
# ]


class WorkDoneProgress(Feature):
    def __init__(self, server: "CustomLanguageServer", parent_config_id: str):
        if server.config is None:
            raise Exception
        if parent_config_id not in server.config.configs:
            raise Exception

        """
        Whether to report progress or not.
        """
        self.is_enabled = False

        """
        This is an identifier that the LSP spec requires in order to consistently update
        asynchronous WorkDoneProgress processes.
        """
        self.token = uuid.uuid4()

        # TODO: Do the search and parsing of custom progress config here

        super().__init__(server, parent_config_id, None)

        self.init()

    def init(self):
        self.is_enabled = self.config.use_lsp_progress

    async def progress_start(self):
        if not self.is_enabled:
            return
        self.is_progressing = True
        self._progress_start()
        # TODO: Custom progress behaviour
        # while self.is_progressing:
        #     # call whatever custom progress configs are defined
        #     await asyncio.sleep(PROGRESS_POLL_RATE)

    async def progress_end(self):
        if not self.is_enabled:
            return

        try:
            self._progress_end()
        finally:
            self.is_progressing = False

    def _progress_start(self):
        # TODO: There's a default message, and a custom one, think about how to do that
        message = f"starting {self.name}"
        self.server.lsp.progress.begin(
            self.token,
            WorkDoneProgressBegin(kind="begin", title=message, percentage=0),
        )

    def _progress_end(self):
        # TODO: There's a default message, and a custom one, think about how to do that
        message = f"ending {self.name}"
        self.server.lsp.progress.end(
            self.token,
            WorkDoneProgressBegin(kind="end", title=message, percentage=100),
        )
