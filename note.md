- problematic link
[37m- Sending CMD 72 of 334:  !play https://cdn.discordapp.com/attachments/741945274901200897/875075008723046410/cheesed.mp4[0m
[37mMessage from 1145148517795512340/dodozean: !play https://cdn.discordapp.com/attachments/741945274901200897/875075008723046410/cheesed.mp4[0m


- stream cannot support playlist. Sol: classify 
[37m- Sending CMD 123 of 334:  !stream https://www.youtube.com/playlist?list=PL42rXizBzbC25pvGACvkUQ8EtZcm30BlF[0m
[37mMessage from 1145148517795512340/dodozean: !stream https://www.youtube.com/playlist?list=PL42rXizBzbC25pvGACvkUQ8EtZcm30BlF[0m
[33mWARNING: Cannot delete message "", message not found[0m
[31m[ERROR:bot] Error in stream: CommandError: Streaming playlists is not yet supported.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 4450, in cmd_stream
    raise exceptions.CommandError(
        "Streaming playlists is not yet supported.",
    )
musicbot.exceptions.CommandError: Streaming playlists is not yet supported.



- only support playlist
[37m- Sending CMD 140 of 334:  !pldump https://www.youtube.com/watch?v=bm48ncbhU10&list=PL80gRr4GwcsznLYH-G_FXnzkP5_cHl-KR[0m
[37mMessage from 1145148517795512340/dodozean: !pldump https://www.youtube.com/watch?v=bm48ncbhU10&list=PL80gRr4GwcsznLYH-G_FXnzkP5_cHl-KR[0m
[31m[ERROR:bot] Error in pldump: CommandError: This does not seem to be a playlist.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6340, in cmd_pldump
    raise exceptions.CommandError("This does not seem to be a playlist.")




- url not valid
[37m- Sending CMD 150 of 334:  !pldump slippery people talking heads live 84[0m
[37mMessage from 1145148517795512340/dodozean: !pldump slippery people talking heads live 84[0m
[31m[ERROR:bot] Error in pldump: CommandError: The given URL was not a valid URL.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6324, in cmd_pldump
    raise exceptions.CommandError(
        "The given URL was not a valid URL.",
    )
musicbot.exceptions.CommandError: The given URL was not a valid URL.





- redundant testing command
[37m- Sending CMD 193 of 334:  !repeat on[0m
[37mMessage from 1145148517795512340/dodozean: !repeat on[0m
[37m- Sending CMD 194 of 334:  !repeat off[0m
[37mMessage from 1145148517795512340/dodozean: !repeat off[0m
[37m- Sending CMD 195 of 334:  !repeat off[0m
[37mMessage from 1145148517795512340/dodozean: !repeat off[0m
[31m[ERROR:bot] Error in repeat: CommandError: The player is not currently looping.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 3965, in cmd_repeat
    raise exceptions.CommandError("The player is not currently looping.")
musicbot.exceptions.CommandError: The player is not currently looping.
[37m- Sending CMD 196 of 334:  !repeat off[0m
[37mMessage from 1145148517795512340/dodozean: !repeat off[0m
[31m[ERROR:bot] Error in repeat: CommandError: The player is not currently looping.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 3965, in cmd_repeat
    raise exceptions.CommandError("The player is not currently looping.")
musicbot.exceptions.CommandError: The player is not currently looping.


- potential bug! great!
[37m- Sending CMD 197 of 334:  !cache [0m
[37mMessage from 1145148517795512340/dodozean: !cache[0m
[37m- Sending CMD 198 of 334:  !cache info[0m
[37mMessage from 1145148517795512340/dodozean: !cache info[0m
[37m- Sending CMD 199 of 334:  !cache clear[0m
[37mMessage from 1145148517795512340/dodozean: !cache clear[0m
[31m[ERROR:bot] Error in cache: CommandError: **Failed** to delete cache, check logs for more info...[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 173, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6041, in cmd_cache
    raise exceptions.CommandError(
        "**Failed** to delete cache, check logs for more info...",
    )
musicbot.exceptions.CommandError: **Failed** to delete cache, check logs for more info...



- add blockuser, nice to have 
[37m- Sending CMD 243 of 334:  !blockuser + @MovieBotTest#5179[0m
[37mMessage from 1145148517795512340/dodozean: !blockuser + @MovieBotTest#5179[0m
[31m[ERROR:bot] Error in blockuser: CommandError: MusicBot could not find the user(s) you specified.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 3039, in cmd_blockuser
    raise exceptions.CommandError(
        "MusicBot could not find the user(s) you specified.",
    )
musicbot.exceptions.CommandError: MusicBot could not find the user(s) you specified.



- option may be outdated
[37m- Sending CMD 257 of 334:  !option [0m
[37mMessage from 1145148517795512340/dodozean: !option[0m
[37m- Sending CMD 258 of 334:  !option autoplaylist on[0m
[37mMessage from 1145148517795512340/dodozean: !option autoplaylist on[0m
[31m[ERROR:bot] Error in option: CommandError: The option command is deprecated, use the config command instead.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 173, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 5964, in cmd_option
    raise exceptions.CommandError(
        "The option command is deprecated, use the config command instead.",
    )
musicbot.exceptions.CommandError: The option command is deprecated, use the config command instead.



- what's the meaning of setprefix?

[37m- Sending CMD 266 of 334:  !setprefix [0m
[37mMessage from 1145148517795512340/dodozean: !setprefix[0m
[37m- Sending CMD 267 of 334:  !setprefix **[0m
[37mMessage from 1145148517795512340/dodozean: !setprefix **[0m
[31m[ERROR:bot] Error in setprefix: CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6954, in cmd_setprefix
    raise exceptions.CommandError(
    ...<2 lines>...
    )
musicbot.exceptions.CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.
[37m- Sending CMD 268 of 334:  !setprefix **[0m
[37mMessage from 1145148517795512340/dodozean: !setprefix **[0m
[31m[ERROR:bot] Error in setprefix: CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6954, in cmd_setprefix
    raise exceptions.CommandError(
    ...<2 lines>...
    )
musicbot.exceptions.CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.
[37m- Sending CMD 269 of 334:  !setprefix ?[0m
[37mMessage from 1145148517795512340/dodozean: !setprefix ?[0m
[31m[ERROR:bot] Error in setprefix: CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 6954, in cmd_setprefix
    raise exceptions.CommandError(
    ...<2 lines>...
    )
musicbot.exceptions.CommandError: Prefix per server is not enabled!
Use the config command to update the prefix instead.



- developer TODOs, nice to have
[37mMessage from 1145148517795512340/dodozean: !setcookies[0m
[31m[ERROR:bot] Error in setcookies: CommandError: No attached uploads were found, try again while uploading a cookie file.[0m
Traceback (most recent call last):
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 8218, in on_message
    response = await handler(**handler_kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 173, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/utils.py", line 254, in wrapper
    return await func(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dodozean/EECS481/MusicBot/musicbot/bot.py", line 7877, in cmd_setcookies
    raise exceptions.CommandError(
        "No attached uploads were found, try again while uploading a cookie file."
    )
musicbot.exceptions.CommandError: No attached uploads were found, try again while uploading a cookie file.

- seek issue