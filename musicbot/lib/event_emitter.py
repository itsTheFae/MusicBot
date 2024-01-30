import asyncio
import collections
import traceback
from typing import Any, Callable, DefaultDict, List

EventCallback = Callable[..., Any]
EventList = List[EventCallback]
EventDict = DefaultDict[str, EventList]


class EventEmitter:
    def __init__(self) -> None:
        self._events: EventDict = collections.defaultdict(list)
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        if event not in self._events:
            return

        for cb in list(self._events[event]):
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.ensure_future(cb(*args, **kwargs), loop=self.loop)
                else:
                    cb(*args, **kwargs)

            except Exception:  # pylint: disable=broad-exception-caught
                traceback.print_exc()

    def on(self, event: str, cb: EventCallback) -> Any:
        self._events[event].append(cb)
        return self

    def off(self, event: str, cb: EventCallback) -> Any:
        self._events[event].remove(cb)

        if not self._events[event]:
            del self._events[event]

        return self

    def once(self, event: str, cb: EventCallback) -> Any:
        def callback(*args: Any, **kwargs: Any) -> Any:
            self.off(event, callback)
            return cb(*args, **kwargs)

        return self.on(event, callback)
