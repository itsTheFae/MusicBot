# MusicBot Translation Guide  

[![Crowdin](https://badges.crowdin.net/notmusicbot/localized.svg)](https://crowdin.com/project/notmusicbot)

Visit [Crowdin](https://crowdin.com/project/notmusicbot/) to get the latest available translations, or help MusicBot with translations.

MusicBot makes use of GNU gettext for translation of display text.  
We use the typical `.po`/`.mo` format to enable translations.  
Language directories in `./i18n/` should be named using lower-case, and mostly conform to the [Locale-Names specification](https://www.gnu.org/savannah-checkouts/gnu/gettext/manual/html_node/Locale-Names.html) by gettext.  

By default, MusicBot will detect and use your system language, if translations are available.  
To set a specific language, MusicBot provides these launch options:  

- `--log_lang=xx`  
  To set log language only.  
- `--msg_lang=xx`  
  To set discord default language only.  
- `--lang=xx`  
  To set both log and discord language at once.  

Replace `xx` above with the lower-case locale code or list of codes of your choice. Only one language code can be set using these options.  
For more info on these, use the `--help` launch option.

## How MusicBot loads translations  

MusicBot will detect your system or environment language(s) setting and attempts to load the language it detects if no language is explicitly set via the launch options.  

At start-up, MusicBot looks for language files based on a longest-match first.  
For example, assume your system language is `en_GB`.  
When MusicBot starts, it will scan `./i18n/en_GB/LC_MESSAGES/` for translation files with the `.mo` extension. If that fails, bot will look for a shorter version of the language code, in this case just `./i18n/en/...` instead.  

Note that the locale codes are case-sensitive, and MusicBot will look for a directory with the exact code you provide.

> On unix-like (Linux / Mac) systems, MusicBot makes use of the Environment Variables: `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG` in that order.  
The first variable with a non-empty value is selected, and multiple languages may be specified by separating them with a colon `:` character.

## How to add a new Language  

Adding a new language to MusicBot requires extra tools, like the GNU Gettext utilities or an application like PoEdit. These are needed to extract strings and compile the `.mo` binary catalog files from their `.po` or `.pot` text files.  

Otherwise, the process is relatively easy, and can be done in a few steps:  

1. Pick a language code. For example: `es_ES` as in Spanish of Spain.  
2. Create the new language directories. Ex.: `./i18n/es_ES/LC_MESSAGES/`  
3. Copy an existing `.po` or run `extract.sh` to make an empty translations `.pot` file.  
4. Translate the strings and save the `.po` and `.mo` files using a tool like PoEdit or other gettext tools.
5. Copy the `.mo` file to the directory made in step 2.
6. Test your translations by launching with `run.sh --lang=es_ES`  

>**NOTE:**   
Picking an appropriate language code or [Locale-Name](https://www.gnu.org/savannah-checkouts/gnu/gettext/manual/html_node/Locale-Names.html) for the language can be a little complicated.  
As MusicBot will detect the system / environment language automatically, some consideration must be given to what code(s) each system might report for a specific language.  
While Spanish in Spain (`es_ES`) may be different from Spanish in Mexico (`es_MX`) adding Spanish as `es` will cover both locales until a more specific translation is added.  

## Working with translation strings  

While translation is the name of the game, the same tools can be used for simple customization of the MusicBot output as well.  You can change almost anything about the text output without needing to edit code!

If you've never heard of Gettext before, getting started might be a little confusing.  For developers and users alike, you may find many answers to your questions within the [GNU Gettext manual](https://www.gnu.org/software/gettext/manual/index.html)  

However, the basics are:

- Files ending with `.pot` are templates, containing all the source strings but no translations.  
  Plain text files that you edit to make `.po` files.
- Files ending with `.po` are fully or partially translated templates with specific language code and meta data set.  
  Also plain-text, multiple speakers of the selected language may contribute to this file.
- Files ending with `.mo` are compiled binary versions of the `.po` file, that make translation at runtime possible.  
  MusicBot only looks for these when loading translations.
- All changes to translations must be compiled into a `.mo` file before you can see them.
- Translations must not change or add placeholders, but may remove them entirely if needed.

Regarding "placeholders", MusicBot sometimes needs to include variable data in output strings.  
To do this, we use traditional percent or modulo (`%`) formatting placeholders in Python that resembles C-style `sprintf` string formatting.  
These placeholders can be removed from translated strings but must not be changed or added.  Placeholders with no association in the source code will cause errors.  
For details on how this style of formatting works, check out the [printf-style string formatting](https://docs.python.org/3.10/library/stdtypes.html#printf-style-string-formatting) section of the python manual.

### Updating Source Strings

While working on MusicBot you might want to change some text in the source or add new strings for translation.  
There are some important things to remember when changing strings in source code:  

1. The string in the source code is the `msgid` in the po files.  
  If the source string changes, the `msgid` is invalid and new translation is needed for each language.

2. MusicBot has two different message domains. One for text in the logs and the other for text sent to discord.

3. Certain objects or function calls will mark strings as translatable but do not immediately translate them:  

   1. All `log.*()` methods mark strings translatable in log domain.  
      Translation is deferred until output time in the logger.
   2. Functions `_L` and `_Ln` mark and immediately translate in the log domain.
   3. Exceptions based on `MusicbotException` provide marking in both domains, but translation in a specific domain must be explicitly called when they are handled.  
   4. Function `_X` only marks in both domains, similar to Exceptions above.
   5. Functions `_D` and `_Dn` mark and immediately translate in the discord domain. While `_Dd` will only mark for deferred translation.
   6. The `_D` and `_Dn` functions require an optional `GuildSpecificData` to enable per-server language selection.

4. Finally, all changes and additional strings need to be extracted before they can be translated.  


If you already have the gettext tools installed on your system, the script `./i18n/extract.sh` can be used to extract properly marked strings from the source code and create `.pot` files with the results.  

If you can't use gettext or want to use another gettext compatible tool for extraction, you'll want to open the above script in a text editor and use its gettext options to adjust your own settings.

### Testing Translations
For developers adding new strings to MusicBot, we provide another script to generate a testing language using extracted strings. To use this script you'll need both gettext tools and the python package `polib` or it will fail to work.

The script `./i18n/mktestlang.sh` will perform an extraction and conversion of strings to reversed variations. The test language is stored inside of `./i18n/xx/LC_MESSAGES/` and can then be enabled by passing `--lang=xx` as a launch option.  

While the test language is enabled, all translated strings should appear as reversed text.  This makes it easier to check if your strings have been correctly marked and included for translation.  Just keep in mind, some text from external libraries may not be translated or may require extra steps to translate if needed.  

