from typing import TYPE_CHECKING, Callable, Any, Optional, List

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

import asyncio
import time
import logging

DeferredFunction = Callable[[], Any]


# TODO: Consider refactoring outside of custom, to be part of the template. Or indeed put it
# in Pygls itself?
class Debounce:
    """
    General functionality to help with various forms of debouncing. Deboucning is essentially a
    technique to prevent unnecessarily rapid calls to expensive code.
    """

    def __init__(
        self,
        key: str,
        period: int,
        function: Optional[DeferredFunction] = None,
        args: Optional[List[Any]] = None,
    ):
        self.key = key
        self.period = period
        self.function = function
        self.args = args
        self.is_deferring: bool = False
        self.triggered_at: Optional[int] = None

    @classmethod
    def init(
        cls,
        server: "CustomLanguageServer",
        config_id: str,
        key: str,
        function: Optional[DeferredFunction] = None,
        args: Optional[List[Any]] = None,
    ):
        if server.configuration is None:
            raise Exception

        period = server.configuration.configs[config_id].debounce
        if period is None:
            # TODO: `period` isn't optional, maybe change `server.config` type to `Config`?
            raise Exception
        if key in server.debounces:
            return

        server.debounces[key] = Debounce(key, period, function, args)

    def is_debounced(self):
        if self.triggered_at is None:
            self.reset()
            return False

        elapsed = self.milliseconds_now() - self.triggered_at
        logging.debug(f"Debouncer: `elapsed`: {elapsed}, `self.period`: {self.period}")
        if elapsed <= self.period:
            logging.debug(f"Debouncing: {self.key} ({elapsed}ms)")
            if self.is_deferrable() and not self.is_deferring:
                self.defer()
            return True

        self.reset()
        return False

    def milliseconds_now(self):
        return time.time() * 1000

    def reset(self):
        self.triggered_at = self.milliseconds_now()

    def is_deferrable(self):
        return self.function is not None

    def defer(self):
        self.is_deferring = True
        asyncio.create_task(self.deferred_run())

    async def deferred_run(self):
        logging.debug(
            f"Debounce deferring: {self.function}({self.args}) in {self.period}ms"
        )
        await asyncio.sleep(self.period / 1000)
        try:
            logging.debug(
                f"Debounce calling deferred function: {self.function}({self.args})"
            )
            if self.args is not None:
                await self.function(*self.args)
            else:
                await self.function()
        except Exception as error:
            raise error
        finally:
            self.is_deferring = False
