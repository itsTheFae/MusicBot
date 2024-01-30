import datetime
import logging
from collections import deque
from itertools import islice
from random import shuffle
from typing import (
    TYPE_CHECKING,
    Any,
    Deque,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

from .constructs import Serializable
from .entry import StreamPlaylistEntry, URLPlaylistEntry
from .exceptions import ExtractionError, InvalidDataError, WrongEntryTypeError
from .lib.event_emitter import EventEmitter

if TYPE_CHECKING:
    import asyncio

    import aiohttp
    import discord

    from .bot import MusicBot
    from .downloader import YtdlpResponseDict
    from .player import MusicPlayer

# type aliases
EntryTypes = Union[URLPlaylistEntry, StreamPlaylistEntry]

log = logging.getLogger(__name__)


class Playlist(EventEmitter, Serializable):
    """
    A playlist that manages the list of songs that will be played.
    """

    def __init__(self, bot: "MusicBot") -> None:
        if bot.session is None:
            raise RuntimeError(
                "Attempt to make Playlist object without aiohttp session. This should never happen..."
            )

        super().__init__()
        self.bot: "MusicBot" = bot
        self.loop: "asyncio.AbstractEventLoop" = bot.loop
        self.aiosession: "aiohttp.ClientSession" = bot.session
        self.entries: Deque[EntryTypes] = deque()

    def __iter__(self) -> Iterator[EntryTypes]:
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def shuffle(self) -> None:
        shuffle(self.entries)

    def clear(self) -> None:
        self.entries.clear()

    def get_entry_at_index(self, index: int) -> EntryTypes:
        self.entries.rotate(-index)
        entry = self.entries[0]
        self.entries.rotate(index)
        return entry

    def delete_entry_at_index(self, index: int) -> EntryTypes:
        """Remove and return the entry at the given index."""
        # TODO: maybe lock all queue management?
        self.entries.rotate(-index)
        entry = self.entries.popleft()
        self.entries.rotate(index)
        return entry

    def insert_entry_at_index(self, index: int, entry: EntryTypes) -> None:
        """Add entry to the queue at the given index."""
        self.entries.rotate(-index)
        self.entries.appendleft(entry)
        self.entries.rotate(index)

    async def add_stream_from_info(
        self,
        info: "YtdlpResponseDict",
        *,
        head: bool = False,
        defer_serialize: bool = False,
        **meta: Any,
    ) -> Tuple[StreamPlaylistEntry, int]:
        # TODO: A bit more validation, "~stream some_url" should not just say :ok_hand:
        # @Fae: about as much validation we can do is making sure the URL is playable.
        # Users are using stream to play without downloading, and enforcing a check
        # for "streaming" media here would break that use case.

        log.noise(  # type: ignore[attr-defined]
            f"Adding stream entry for URL:  {info.url}"
        )
        entry = StreamPlaylistEntry(
            self,
            info,
            **meta,
        )
        self._add_entry(entry, head=head, defer_serialize=defer_serialize)
        return entry, len(self.entries)

    async def add_entry_from_info(
        self,
        info: "YtdlpResponseDict",
        *,
        head: bool = False,
        defer_serialize: bool = False,
        **meta: Any,
    ) -> Tuple[EntryTypes, int]:
        """
        Validates extracted info and adds media to be played.
        This does not start the download of the song.

        :param info: The extraction data of the song to add to the playlist.
        :param head: Add to front of queue instead.
        :param meta: Any additional metadata to add to the playlist entry.
        :returns: the entry & the position it is in the queue.
        :raises: ExtractionError, WrongEntryTypeError
        """

        if not info:
            raise ExtractionError("Could not extract information")

        # TODO: Sort out what happens next when this happens
        if info.ytdl_type == "playlist":
            raise WrongEntryTypeError(
                "This is a playlist.",
                True,
                info.webpage_url or info.url,
            )

        # check if this is a stream, just in case.
        if info.is_stream:
            log.debug("Entry info appears to be a stream, adding stream entry...")
            return await self.add_stream_from_info(info, head=head, **meta)

        # TODO: Extract this to its own function
        if info.extractor in ["generic", "Dropbox"]:
            content_type = info.http_header("content-type", None)

            if content_type:
                if content_type.startswith(("application/", "image/")):
                    if not any(x in content_type for x in ("/ogg", "/octet-stream")):
                        # How does a server say `application/ogg` what the actual fuck
                        raise ExtractionError(
                            f'Invalid content type "{content_type}" for url: {info.url}'
                        )

                elif (
                    content_type.startswith("text/html") and info.extractor == "generic"
                ):
                    log.warning(
                        "Got text/html for content-type, this might be a stream."
                    )
                    return await self.add_stream_from_info(info, head=head, **meta)
                    # TODO: Check for shoutcast/icecast

                elif not content_type.startswith(("audio/", "video/")):
                    log.warning(
                        'Questionable content-type "%s" for url:  %s',
                        content_type,
                        info.url,
                    )

        log.noise(  # type: ignore[attr-defined]
            f"Adding URLPlaylistEntry for: {info.get('__input_subject')}"
        )
        entry = URLPlaylistEntry(self, info, **meta)
        self._add_entry(entry, head=head, defer_serialize=defer_serialize)
        return entry, (1 if head else len(self.entries))

    async def import_from_info(
        self, info: "YtdlpResponseDict", head: bool, **meta: Any
    ) -> Tuple[List[EntryTypes], int]:
        """
        Imports the songs from `info` and queues them to be played.

        Returns a list of `entries` that have been enqueued.

        :param playlist_url: The playlist url to be cut into individual urls and added to the playlist
        :param meta: Any additional metadata to add to the playlist entry
        """
        position = 1 if head else len(self.entries) + 1
        entry_list = []
        baditems = 0
        entries = info.get_entries_objects()
        author_perms = None
        author = meta.get("author", None)
        defer_serialize = True

        if author:
            author_perms = self.bot.permissions.for_user(author)

        if head:
            entries.reverse()

        track_number = 0
        for item in entries:
            # count tracks regardless of conditions, used for missing track names
            # and also defers serialization of the queue for playlists.
            track_number += 1
            # Exclude entries over max permitted duration.
            if (
                author_perms
                and author_perms.max_song_length
                and item.duration > author_perms.max_song_length
            ):
                log.debug(
                    "Ignoring song in entries by '%s', duration longer than permitted maximum.",
                    author,
                )
                baditems += 1
                continue

            # Check youtube data to pre-emptively avoid adding Private or Deleted videos to the queue.
            if info.extractor.startswith("youtube") and (
                "[private video]" == item.get("title", "").lower()
                or "[deleted video]" == item.get("title", "").lower()
            ):
                log.warning(
                    "Not adding youtube video because it is marked private or deleted:  %s",
                    item.get_playable_url(),
                )
                baditems += 1
                continue

            # Soundcloud playlists don't get titles in flat extraction. A bug maybe?
            # Anyway we make a temp title here, the real one is fetched at play.
            if "title" in info and "title" not in item:
                item["title"] = f"{info.title} - #{track_number}"

            if track_number >= info.entry_count:
                defer_serialize = False

            try:
                entry, _pos = await self.add_entry_from_info(
                    item, head=head, defer_serialize=defer_serialize, **meta
                )
                entry_list.append(entry)
            except (WrongEntryTypeError, ExtractionError):
                baditems += 1
                log.warning("Could not add item")
                log.debug("Item: %s", item, exc_info=True)

        if baditems:
            log.info("Skipped %s bad entries", baditems)

        if head:
            entry_list.reverse()
        return entry_list, position

    def get_next_song_from_author(
        self, author: "discord.abc.User"
    ) -> Optional[EntryTypes]:
        for entry in self.entries:
            if entry.meta.get("author", None) == author:
                return entry

        return None

    def reorder_for_round_robin(self) -> None:
        """
        Reorders the queue for round-robin
        """
        new_queue: Deque[EntryTypes] = deque()
        all_authors: List["discord.User"] = []

        for entry in self.entries:
            author = entry.meta.get("author", None)
            if author and author not in all_authors:
                all_authors.append(author)

        request_counter = 0
        song: Optional[EntryTypes] = None
        while self.entries:
            if request_counter == len(all_authors):
                request_counter = 0

            song = self.get_next_song_from_author(all_authors[request_counter])

            if song is None:
                all_authors.pop(request_counter)
                continue

            new_queue.append(song)
            self.entries.remove(song)
            request_counter += 1

        self.entries = new_queue

    def _add_entry(
        self, entry: EntryTypes, *, head: bool = False, defer_serialize: bool = False
    ) -> None:
        if head:
            self.entries.appendleft(entry)
        else:
            self.entries.append(entry)

        if self.bot.config.round_robin_queue:
            self.reorder_for_round_robin()

        self.emit(
            "entry-added", playlist=self, entry=entry, defer_serialize=defer_serialize
        )

        if self.peek() is entry:
            entry.get_ready_future()

    async def _try_get_entry_future(
        self, entry: EntryTypes, predownload: bool = False
    ) -> Any:
        """gracefully try to get the entry ready future, or start pre-downloading one."""
        moving_on = " Moving to the next entry..."
        if predownload:
            moving_on = ""

        try:
            if predownload:
                entry.get_ready_future()
            else:
                return await entry.get_ready_future()

        except ExtractionError as e:
            log.warning("Extraction failed for a playlist entry.%s", moving_on)
            self.emit("entry-failed", entry=entry, error=e)
            if not predownload:
                return await self.get_next_entry()

        except AttributeError as e:
            log.warning(
                "Deserialize probably failed for a playlist entry.%s",
                moving_on,
            )
            self.emit("entry-failed", entry=entry, error=e)
            if not predownload:
                return await self.get_next_entry()

        return None

    async def get_next_entry(self, predownload_next: bool = True) -> Any:
        """
        A coroutine which will return the next song or None if no songs left to play.

        Additionally, if predownload_next is set to True, it will attempt to download the next
        song to be played - so that it's ready by the time we get to it.
        """
        if not self.entries:
            return None

        entry = self.entries.popleft()

        if predownload_next:
            next_entry = self.peek()
            if next_entry:
                await self._try_get_entry_future(next_entry, predownload_next)

        return await self._try_get_entry_future(entry)

    def peek(self) -> Optional[EntryTypes]:
        """
        Returns the next entry that should be scheduled to be played.
        """
        if self.entries:
            return self.entries[0]
        return None

    async def estimate_time_until(
        self, position: int, player: "MusicPlayer"
    ) -> datetime.timedelta:
        """
        (very) Roughly estimates the time till the queue will reach given `position`.

        :param: position:  The index in the queue to reach.
        :param: player:  MusicPlayer instance this playlist should belong to.

        :returns: A datetime.timedelta object with the estimated time.

        :raises: musicbot.exceptions.InvalidDataError  if duration data cannot be calculated.
        """
        # TODO: double check the way we deal with time again.  I've messed something up.
        if any(e.duration is None for e in islice(self.entries, position - 1)):
            raise InvalidDataError("no duration data")

        estimated_time = sum(
            float(e.duration_td.seconds) for e in islice(self.entries, position - 1)
        )

        # When the player plays a song, it eats the first playlist item, so we just have to add the time back
        if not player.is_stopped and player.current_entry:
            if player.current_entry.duration is None:  # duration can be 0
                raise InvalidDataError("no duration data in current entry")

            estimated_time += player.current_entry.duration - player.progress

        return datetime.timedelta(seconds=estimated_time)

    def count_for_user(self, user: "discord.abc.User") -> int:
        return sum(1 for e in self.entries if e.meta.get("author", None) == user)

    def __json__(self) -> Dict[str, Any]:
        return self._enclose_json({"entries": list(self.entries)})

    @classmethod
    def _deserialize(
        cls, raw_json: Dict[str, Any], bot: Optional["MusicBot"] = None, **kwargs: Any
    ) -> "Playlist":
        assert bot is not None, cls._bad("bot")
        # log.debug("Deserializing playlist")
        pl = cls(bot)

        for entry in raw_json["entries"]:
            pl.entries.append(entry)

        # TODO: create a function to init downloading (since we don't do it here)?
        return pl
