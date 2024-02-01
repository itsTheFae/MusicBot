import inspect
import json
import logging
import pydoc
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Set, Type, Union

from .utils import _get_variable

if TYPE_CHECKING:
    from discord import Embed, Message

log = logging.getLogger(__name__)


class SkipState:
    __slots__ = ["skippers", "skip_msgs"]

    def __init__(self) -> None:
        """
        Manage voters and their ballots for fair MusicBot track skipping.
        This creates a set of discord.Message and a set of member IDs to
        enable counting votes for skipping a song.
        """
        self.skippers: Set[int] = set()
        self.skip_msgs: Set["Message"] = set()

    @property
    def skip_count(self) -> int:
        """
        Get the number of authors who requested skip.
        """
        return len(self.skippers)

    def reset(self) -> None:
        """
        Clear the vote counting sets.
        """
        self.skippers.clear()
        self.skip_msgs.clear()

    def add_skipper(self, skipper_id: int, msg: "Message") -> int:
        """
        Add a message and the author's ID to the skip vote.
        """
        self.skippers.add(skipper_id)
        self.skip_msgs.add(msg)
        return self.skip_count


class Response:
    __slots__ = ["_content", "reply", "delete_after", "codeblock", "_codeblock"]

    def __init__(
        self,
        content: Union[str, "Embed"],
        reply: bool = False,
        delete_after: int = 0,
        codeblock: str = "",
    ) -> None:
        """
        Helper class intended to be used by command functions in MusicBot.
        Simple commands should return a Response rather than calling to send
        messages on their own.

        :param: content:  the text message or an Embed object to be sent.
        :param: reply:  if this response should reply to the original author.
        :param: delete_after:  how long to wait before deleting the message created by this Response.
            Set to 0 to never delete.
        :param: codeblock:  format a code block with this value as the language used for syntax highlights.
        """
        self._content = content
        self.reply = reply
        self.delete_after = delete_after
        self.codeblock = codeblock
        self._codeblock = f"```{codeblock}\n{{}}\n```"

    @property
    def content(self) -> Union[str, "Embed"]:
        """
        Get the Response content, but quietly format a code block if needed.
        """
        if self.codeblock:
            return self._codeblock.format(self._content)
        return self._content


class Serializer(json.JSONEncoder):
    def default(self, o: "Serializable") -> Any:
        """
        Default method used by JSONEncoder to return serializable data for
        the given object or Serializable in `o`
        """
        if hasattr(o, "__json__"):
            return o.__json__()

        return super().default(o)

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Any:
        """
        Read a simple JSON dict for a valid class signature, and pass the
        simple dict on to a _deserialize function in the signed class.
        """
        if all(x in data for x in Serializable.CLASS_SIGNATURE):
            # log.debug("Deserialization requested for %s", data)
            factory = pydoc.locate(data["__module__"] + "." + data["__class__"])
            # log.debug("Found object %s", factory)
            if factory and issubclass(factory, Serializable):  # type: ignore[arg-type]
                # log.debug("Deserializing %s object", factory)
                return factory._deserialize(  # type: ignore[attr-defined]
                    data["data"], **cls._get_vars(factory._deserialize)  # type: ignore[attr-defined]
                )

        return data

    @classmethod
    def _get_vars(cls, func: Callable[..., Any]) -> Dict[str, Any]:
        """
        Inspect argument specification for given callable `func` and attempt
        to inject it's named parameters by inspecting the calling frames for
        locals which match the parameter names.
        """
        # log.debug("Getting vars for %s", func)
        params = inspect.signature(func).parameters.copy()
        args = {}
        # log.debug("Got %s", params)

        for name, param in params.items():
            # log.debug("Checking arg %s, type %s", name, param.kind)
            if param.kind is param.POSITIONAL_OR_KEYWORD and param.default is None:
                # log.debug("Using var %s", name)
                args[name] = _get_variable(name)
                # log.debug("Collected var for arg '%s': %s", name, args[name])

        return args


class Serializable:
    CLASS_SIGNATURE = ("__class__", "__module__", "data")

    def _enclose_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper used by child instances of Serializable that includes class signature
        for the Serializable object.
        Intended to be called from __json__ methods of child instances.
        """
        return {
            "__class__": self.__class__.__qualname__,
            "__module__": self.__module__,
            "data": data,
        }

    # Perhaps convert this into some sort of decorator
    @staticmethod
    def _bad(arg: str) -> None:
        """
        Wrapper used by assertions in Serializable classes to enforce required arguments.

        :param: arg:  the parameter name being enforced.

        :raises: TypeError  when given `arg` is None in calling frame.
        """
        raise TypeError(f"Argument '{arg}' must not be None")

    def serialize(self, *, cls: Type[Serializer] = Serializer, **kwargs: Any) -> str:
        """
        Simple wrapper for json.dumps with Serializer instance support.
        """
        return json.dumps(self, cls=cls, **kwargs)

    def __json__(self) -> Optional[Dict[str, Any]]:
        """
        Serialization method to be implemented by derived classes.
        Should return a simple dictionary representing the Serializable
        class and its data/state, using only built-in types.
        """
        raise NotImplementedError

    @classmethod
    def _deserialize(
        cls: Type["Serializable"], raw_json: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """
        Deserialization handler, to be implemented by derived classes.
        Should construct and return a valid Serializable child instance or None.

        :param: raw_json:  data from json.loads() using built-in types only.
        """
        raise NotImplementedError
