# MusicBot

[![GitHub stars](https://img.shields.io/github/stars/Just-Some-Bots/MusicBot.svg)](https://github.com/Just-Some-Bots/MusicBot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Just-Some-Bots/MusicBot.svg)](https://github.com/Just-Some-Bots/MusicBot/network)
[![Python version](https://img.shields.io/badge/python-3.8%2C%203.9%2C%203.10%2C%203.11-blue.svg)](https://python.org)
[![Discord](https://discordapp.com/api/guilds/129489631539494912/widget.png?style=shield)](https://discord.gg/bots)

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

- Add actual command-line arguments to control logging, show version, and skip startup checks.
  - Update logging to defer log file creation until the first log is emitted.
  - Update log file rotation to use file modification time, not just sort by filename.
  - Allow CLI log-level to override log level set in config/options.ini.
- Playing compound links now works better and does not double-queue the carrier video.
- Majority of function definitions now have some kind of docstring.
- Enforce code checks using `Pylint` and `isort` to reduce inconsistency and clean up code.
- Ensure source code complies with mypy checks, and fix various bugs on the way.
  - Updates MusicBot logging to enable time-based log files and safely close the logs in most cases.
  - Removes `shlex` from the `search` command, search engines now handle quotes directly.
  - Fixes possible issues with counting members in channel not respecting bot exceptions.
  - Updates ConfigParser to provide extra parser methods rather than relying on validation later.
  - Updates Permissions to also use extended ConfigParser methods, for consistency.
  - Adds requirements.dev.txt for all the bells and whistles, mostly for devs.
  - Refactored the decorator methods to live in utils.py or be removed.
- Complete overhaul of ytdl information extraction and several player commands, performance focused.  
  - Updates `shuffleplay` to shuffle playlist entries before they are queued.
  - Adds playlist name and other details to `pldump` generated files.
  - Enable `pldump` command to send file to invoking channel if DM fails.
  - Updates Now Playing Status to use custom status and activity *(experimental)*.
  - Adds stream support to autoplaylist entries, if they are detected as a stream.
  - Adds stream support to regular play command, if input is detected as a stream.
  - Adds playlist link support to autoplaylist entries. *(experimental)*
  - Asks if user wants to queue the playlist when using links with playlist and video IDs.
  - Include thumbnail in now-playing for any tracks that have it.
  - Remove all extraneous calls to extract_info, and carry extracted info with entries.
  - Rebuild of Spotify API to make it faster to enqueue Spotify playlists and albums.  
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
