# MusicBot i18n Guide
MusicBot makes use of GNU gettext for translation of display text.  
We use the typical `.po`/`.mo` format to enable translations.  
Language directories in `i18n/` should be named using lower-case, and mostly conform to the [Locale-Names specification](https://www.gnu.org/savannah-checkouts/gnu/gettext/manual/html_node/Locale-Names.html) by gettext.  

By default, MusicBot will detect and use your system language, if translations are available.  
To set MusicBot as a specific language, you can use any of the following launch options:  
 `--log_lang`  to set log language only.  
 `--msg_lang`  to set discord default language only.  
 `--lang`  to set both at once.  
For more info on these, use the `--help` launch option.

MusicBot will look for languages based on a longest-match first. For example, assume your system language is `en_GB`.  When MusicBot starts, it will scan `i18n/en_gb/LC_MESSAGES/` for translation files. If that fails, bot will look for a shorter version of the language, in this case just `i18n/en/...` instead.  

Multiple language codes can be specified, each separated by a comma, where the first are considered most favored. However, only one language will be used at a time. Translations missing from one language will be returned without translation, rather than checking a different language first.

## Add New Language
Adding new languages to MusicBot is relatively easy, and can be done in a few steps:  
1. Pick a language code. For example: `es_ES` as in Spanish of Spain.  
2. Create the new language directories. Ex.: `./i18n/es_es/LC_MESSAGES/`  
3. Copy an existing `.po` or run `extract.sh` to make empty translations.  
4. Translate the strings and convert the `.po` file to `.mo` using a tool like PoEdit.
5. Test your translations by launching with `run.sh --lang=es_ES`  

**NOTE:**   
Picking an appropriate language code or [Locale-Name](https://www.gnu.org/savannah-checkouts/gnu/gettext/manual/html_node/Locale-Names.html) for the language can be a little complicated.  
As MusicBot will detect the system / environment language automatically, some consideration must be given to what code(s) each system might report for a specific language.  
That being said, it may make sense to use a shorter, less-strict language code in some cases. While Spanish in Spain (`es_ES`) may be different from Spanish in Mexico (`es_MX`) adding Spanish as `es` will cover both variations until a more specific translation is added.  

## Updating Source Strings
While working on MusicBot you might want to change some text or add new strings for translation.  All changes and additional strings need to be extracted before they can be translated.  

For convenience, the script `./i18n/extract.sh` is pre-configured to extract properly marked strings from the source code and create `.po` files with the results.  

## Testing Translations
For developers adding new strings to MusicBot, we provide another script to generate a testing language using extracted strings.  

The script `./i18n/mktestlang.sh` will perform an extraction and conversion of strings to reversed variations. The test language is stored inside of `./i18n/xx/LC_MESSAGES/` and can then be enabled by passing `--lang=xx` as a launch option.  

While the test language is enabled, all translated strings should appear as reversed text.  This makes it easier to check if your strings have been correctly marked and included for translation.  Just keep in mind, some text from external libraries may not be translated or may require extra steps to translate if needed.  

