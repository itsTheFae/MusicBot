import subprocess

VERSION: str = ""
try:
    VERSION = (
        subprocess.check_output(["git", "describe", "--tags", "--always", "--dirty"])
        .decode("ascii")
        .strip()
    )
except Exception:
    VERSION = "version_unknown"

# constant string exempt from i18n
DEFAULT_FOOTER_TEXT: str = f"Just-Some-Bots/MusicBot ({VERSION})"

DEFAULT_MUSICBOT_LOG_FILE: str = "logs/musicbot.log"
DEFAULT_DISCORD_LOG_FILE: str = "logs/discord.log"

DEFAULT_OPTIONS_FILE: str = "config/options.ini"
DEFAULT_PERMS_FILE: str = "config/permissions.ini"
DEFAULT_I18N_FILE: str = "config/i18n/en.json"
DEFAULT_COMMAND_ALIAS_FILE: str = "config/aliases.json"
DEFAULT_BLACKLIST_FILE: str = "config/blacklist.txt"
DEFAULT_WHITELIST_FILE: str = "config/whitelist.txt"
DEFAULT_AUTOPLAYLIST_FILE: str = "config/autoplaylist.txt"
BUNDLED_AUTOPLAYLIST_FILE: str = "config/_autoplaylist.txt"
DEFAULT_AUDIO_CACHE_PATH: str = "audio_cache"

EXAMPLE_OPTIONS_FILE: str = "config/example_options.ini"
EXAMPLE_PERMS_FILE: str = "config/example_permissions.ini"

DISCORD_MSG_CHAR_LIMIT: int = 2000

EMOJI_CHECK_MARK_BUTTON: str = "\u2705"
EMOJI_CROSS_MARK_BUTTON: str = "\u274E"
EMOJI_IDLE_ICON: str = "\U0001f634"  # same as \N{SLEEPING FACE}
EMOJI_PLAY_ICON: str = "\u25B6"  # add \uFE0F to make button
EMOJI_PAUSE_ICON: str = "\u23F8\uFE0F"  # add \uFE0F to make button
