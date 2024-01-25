import shutil
import textwrap
from enum import Enum
from typing import Optional


# Base class for exceptions
class MusicbotException(Exception):
    def __init__(self, message: str, *, expire_in: int = 0) -> None:
        super().__init__(message)  # ???
        self._message = message
        self.expire_in = expire_in

    @property
    def message(self) -> str:
        return self._message

    @property
    def message_no_format(self) -> str:
        return self._message


# Something went wrong during the processing of a command
class CommandError(MusicbotException):
    pass


# Something went wrong during the processing of a song/ytdl stuff
class ExtractionError(MusicbotException):
    pass


# Something is wrong about data
class InvalidDataError(MusicbotException):
    pass


# The no processing entry type failed and an entry was a playlist/vice versa
# TODO: Add typing options instead of is_playlist
class WrongEntryTypeError(ExtractionError):
    def __init__(self, message: str, is_playlist: bool, use_url: str) -> None:
        super().__init__(message)
        self.is_playlist = is_playlist
        self.use_url = use_url


# FFmpeg complained about something
class FFmpegError(MusicbotException):
    pass


# FFmpeg complained about something but we don't care
class FFmpegWarning(MusicbotException):
    pass


# Some issue retrieving something from Spotify's API or processing it.
class SpotifyError(MusicbotException):
    pass


# The user doesn't have permission to use a command
class PermissionsError(CommandError):
    @property
    def message(self) -> str:
        return (
            "You don't have permission to use that command.\nReason: " + self._message
        )


# Error with pretty formatting for hand-holding users through various errors
class HelpfulError(MusicbotException):
    def __init__(
        self,
        issue: str,
        solution: str,
        *,
        preface: str = "An error has occured:",
        footnote: str = "",
        expire_in: int = 0,
    ) -> None:
        self.issue = issue
        self.solution = solution
        self.preface = preface
        self.footnote = footnote
        self.expire_in = expire_in
        self._message_fmt = "\n{preface}\n{problem}\n\n{solution}\n\n{footnote}"

    @property
    def message(self) -> str:
        return self._message_fmt.format(
            preface=self.preface,
            problem=self._pretty_wrap(self.issue, "  Problem:"),
            solution=self._pretty_wrap(self.solution, "  Solution:"),
            footnote=self.footnote,
        )

    @property
    def message_no_format(self) -> str:
        return self._message_fmt.format(
            preface=self.preface,
            problem=self._pretty_wrap(self.issue, "  Problem:", width=0),
            solution=self._pretty_wrap(self.solution, "  Solution:", width=0),
            footnote=self.footnote,
        )

    @staticmethod
    def _pretty_wrap(text: str, pretext: str, *, width: Optional[int] = -1) -> str:
        if width is None:
            return "\n".join((pretext.strip(), text))
        elif width == -1:
            pretext = pretext.rstrip() + "\n"
            width = shutil.get_terminal_size().columns

        lines = textwrap.wrap(text, width=width - 5)
        lines = [
            ("    " + line).rstrip().ljust(width - 1).rstrip() + "\n" for line in lines
        ]

        return pretext + "".join(lines).rstrip()


class HelpfulWarning(HelpfulError):
    pass


# Signal codes used in RestartSignal
class RestartCode(Enum):
    RESTART_SOFT = 0
    RESTART_FULL = 1
    RESTART_UPGRADE_ALL = 2
    RESTART_UPGRADE_PIP = 3
    RESTART_UPGRADE_GIT = 4


# Base class for control signals
class Signal(Exception):
    pass


# signal to restart or reload the bot
class RestartSignal(Signal):
    def __init__(self, code: RestartCode = RestartCode.RESTART_SOFT):
        self.restart_code = code

    def get_code(self) -> int:
        return self.restart_code.value

    def get_name(self) -> str:
        return self.restart_code.name


# signal to end the bot "gracefully"
class TerminateSignal(Signal):
    exit_code: int = 0
