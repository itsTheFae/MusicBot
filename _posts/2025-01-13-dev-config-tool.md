---
title: Config, Tools & More!
type: major
---

> **Notice:** This update is not backwards compatible!  It will update your config and create a backup of the original, just in case.  

**Python support changes**  

In this version, MusicBot officially no longer supports Python 3.8.  
The reason behind this is simple, Python 3.8 has reached End-of-life status and our most important dependency `yt-dlp` no longer supports it.  
To keep using MusicBot, you'll want to upgrade to python 3.9 or any version up to 3.12.  If you are a `dev` branch enjoyer, you may also use python 3.13 (GIL only, free-thread not supported.)  


**OAuth2 integration removed**  

MusicBot previously provided an integration for yt-dlp OAuth2 authorization. 
As this is no longer supported, we have removed the integration and related options 
from MusicBot to help reduce confusion and clutter.  
If somehow that feature was still working for you, another minor change related to 
yt-dlp logging may now allow you to use yt-dlp plugins to replace that feature.


**Config re-organization**  

The file `config/options.ini` and its example file now have more sections, and 
several options have been moved around to better organize the options and hopefully 
make it easier to find options you're looking for.  
Specifically, four new sections have been added:  

 - `[ChatCommands]`  For options related to how MusicBot accepts commands.  
 - `[ChatResponses]`  For options that control how MusicBot responds.  
 - `[Playback]`  For media source and player behavior controls.  
 - `[AutoPlaylist]`  For control of auto-playlist features.  


**Configuration tool**  

A new python tool has been added to MusicBot which replaces the old installer config steps entirely.  
The `configure.py` tool is basically a specialized editor for making configuration changes to MusicBot.  
It can be used at install or the user can call the script under the same python envrionment MusicBot uses to change configurations at any time. 
All changes are saved directly to the config files, and some validation is done on inputs. Changes made while a MusicBot instance is running must be reloaded manually however, by either restarting or using appropriate config/perms reload commands.  

As this is a brand-new tool, it probably has bugs and may not work for every situation. Please consider contributing to improve it as you see fit!  


**More changes**  

Other noteworthy changes include some new options, defaults, or general improvements.  

 - The `play` command(s) can now be used while attaching a file to play it. Previously you needed to copy the link into the play command. This will play only the first attached file.  
 - The `search` command now supports more search services supported by yt-dlp.  
 - New option `DefaultSearchService` can be used to set which service is used for search-based play commands.  
 - New option `ReplyAndMention` can be used to disable author-mentions on responses.  
 - Default of `UseOpusAudio` is now set to yes, as it seems to perform better than PCM.  
 - Removed cookies warning, since it should be obvious...  
 - Fixed `config missing` command producing too much text.  
 - Updated `i18n/lang.py` with new options `-L` and `-A`, check the i18n readme or `--help` option for details.  
 - Updated i18n POT/PO files with new strings and caller related info.  

