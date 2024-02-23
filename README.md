# MusicBot

[![GitHub stars](https://img.shields.io/github/stars/Just-Some-Bots/MusicBot.svg)](https://github.com/Just-Some-Bots/MusicBot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Just-Some-Bots/MusicBot.svg)](https://github.com/Just-Some-Bots/MusicBot/network)
[![Python version](https://img.shields.io/badge/python-3.8%2C%203.9%2C%203.10%2C%203.11%2C%203.12-blue.svg)](https://python.org)
[![Discord](https://discordapp.com/api/guilds/129489631539494912/widget.png?style=shield)](https://discord.gg/bots)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
![Static Badge](https://img.shields.io/badge/Lint-Pylint_and_Flake8-blue?style=flat)


MusicBot is the original Discord music bot written for [Python](https://www.python.org "Python homepage") 3.8+, using the [discord.py](https://github.com/Rapptz/discord.py) library. It plays requested songs from YouTube and other services into a Discord server (or multiple servers). If the queue is empty, MusicBot will play a list of existing songs that is configurable. The bot features a permission system, allowing owners to restrict commands to certain people. MusicBot is capable of streaming live media into a voice channel (experimental).

![Main](https://i.imgur.com/FWcHtcS.png)

## Setup
Setting up the MusicBot is relatively painless - just follow one of the [guides](https://just-some-bots.github.io/MusicBot/). After that, configure the bot to ensure its connection to Discord.

The main configuration file is `config/options.ini`, but it is not included by default. Simply make a copy of `example_options.ini` and rename it to `options.ini`. See [`example_options.ini`](./config/example_options.ini) for more information about configurations.

### Commands

There are many commands that can be used with the bot. Most notably, the `play <url>` command (preceded by your command prefix), which will download, process, and play a song from YouTube or a similar site. A full list of commands is available [here](https://just-some-bots.github.io/MusicBot/using/commands/ "Commands").

### Further reading

* [Support Discord server](https://discord.gg/bots)
* [Project license](LICENSE)

# Fork Change Log

This fork contains changes that may or may not be merged into upstream.  
Cherry-picking (or otherwise copying) is welcome should you feel inclined.  
Here is a list of changes made so far, with most recent first:

- Adds re-try logic to get_player to (hopefully) deal with initial connection failures.
- Changes to player/voice handling to (hopefully) prevent dead players.
- Changes on_ready event to call status update and join channels after the event.
- Further updates to start-up to (hopefully) gracefully fail and install dependencies.
- Adds logic to check for updates to MusicBot via git and for dependencies via pip.  **[merged]**
  - Adds new command `checkupdates` to print status about available updates.
  - Adds new CLI flag `--no-update-check` to disable checking for updates on startup.
  - Adds new CLI flag `--no-install-deps` to disable automatic install of dependencies when ImportError happens.
- Improved security of subprocess command execution, to reduce command/shell injection risks.  **[merged]**
- Updates blocklist feature and adds block list for songs as well as users.  **[merged]**
  - Replaces old `blacklist` command with `blockuser` command.
  - Adds new command `blocksong` which works similarly to `blockuser` command.
  - Updates options.ini to replace or add block list options:
    - Replaces `[Files] Blacklist` with `[Files] UserBlocklistFile` option.
    - Adds `[Files] SongBlocklistFile` option.
    - Adds `[MusicBot] EnableUserBlocklist` to toggle the features. Default enabled.
    - Adds `[MusicBot] EnableSongBlocklist` to toggle the features. Default disabled.
- Auto playlist tracks are auto-skipped when a user adds a new song.  **[merged]**
- Update the `queue` command to add pagination by both command arg and reactions.  **[merged]**
- Allow `listids` and `perms` commands to fall back to sending in public if DM fails.  **[merged]**
- Add actual command-line arguments to control logging, show version, and skip startup checks.  **[merged]**
  - Supported CLI flags:
    - `-V` to print version and exit.
    - `--help` or `-h`  for standard help / usage.
    - `--no-checks`  Legacy option to skip startup checks.
    - `--logs-kept`  Set the number of logs to keep when rotating logs.
    - `--log-level`  Set an override to `DebugLevel` in config/options.ini file.
    - `--log-rotate-fmt`  Set a filename component using strftime() compatible string.
  - Update logging to defer log file creation until the first log is emitted.
  - Update log file rotation to use file modification time, not just sort by filename.
  - Allow CLI log-level to override log level set in config/options.ini.
- Playing compound links now works better and does not double-queue the carrier video.  **[merged]**
- Majority of function definitions now have some kind of docstring.  **[merged]**
- Enforce code checks using `Pylint` and `isort` to reduce inconsistency and clean up code.
- Ensure source code complies with mypy checks, and fix various bugs on the way.
  - Updates MusicBot logging to enable time-based log files and safely close the logs in most cases.  **[merged]**
  - Removes `shlex` from the `search` command, search engines now handle quotes directly.    **[merged]**
  - Fixes possible issues with counting members in channel not respecting bot exceptions.  **[merged]**
  - Updates ConfigParser to provide extra parser methods rather than relying on validation later.  **[merged]**
  - Updates Permissions to also use extended ConfigParser methods, for consistency.  **[merged]**
  - Adds requirements.dev.txt for all the bells and whistles, mostly for devs.
  - Refactored the decorator methods to live in utils.py or be removed.  **[merged]**
- Complete overhaul of ytdl information extraction and several player commands, performance focused.    **[merged]**
  - Updates `shuffleplay` to shuffle playlist entries before they are queued.  **[merged]**
  - Adds playlist name and other details to `pldump` generated files.  **[merged]**
  - Enable `pldump` command to send file to invoking channel if DM fails.  **[merged]**
  - Updates Now Playing Status to use custom status and activity *(experimental)*.  **[merged]**
  - Adds stream support to autoplaylist entries, if they are detected as a stream.  **[merged]**
  - Adds stream support to regular play command, if input is detected as a stream.  **[merged]**
  - Adds playlist link support to autoplaylist entries. *(experimental)*  **[merged]**
  - Asks if user wants to queue the playlist when using links with playlist and video IDs.  **[merged]**
  - Include thumbnail in now-playing for any tracks that have it.  **[merged]**
  - Remove all extraneous calls to extract_info, and carry extracted info with entries.  **[merged]**
  - Rebuild of Spotify API to make it faster to enqueue Spotify playlists and albums.  **[merged]**
- Non-important change of log colors to help set the levels apart.  
- Fix `skip` command to properly tally votes of members.  **[merged]**
- Clean up auto-pause logic to make it less of a mess to look at. **[merged]**
- Automatically un-pause a paused player when using commands that should play something.  **[merged]**
- Attempt to clean up properly in shutdown and restart process.  **[merged]**
- Ensured black and flake8 pass on the entire project source, even currently unused bits.   **[merged]**
  - Cleans up bare except handling which was eating system interrupts and possible other exceptions.
- Updates for `restart` command to enable full restarts and upgrades remotely. *(semi-experimental)*  **[merged]**  
- Automatic fix using certifi when local SSL store is missing certs (mostly a windows bug).  **[merged]**
- Allow use of `autoplaylist` command without a player in voice channel.  **[merged]**
- Preserve autoplaylist.txt formatting and comments, enables "removing" links in-place.  **[merged]**
- Additional option to retain autoplaylist downloads in cache regardless of other cache configs.  **[merged]**
- Improved audio cache management, settings to limit storage use and `cache` command to see info or manually clear it. **[merged]**  
- Per-Server command prefix settings available via new `setprefix` command. Allows almost anything to be a prefix! **[merged]**  
- Player inactivity timer options to auto-disconnect when the player is not playing for a set period of time. **[merged]**  

:)
