#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")" || { echo "failed to change directory"; exit 1; }
cd .. || { echo "failed to change directory"; exit 1; }

MB_Version="$(git describe --tags --always)"

echo "Extracting strings for translation from MusicBot $MB_Version"

echo "Log domain..."
xgettext -v -F -k --language=Python --no-wrap \
    --add-comments="TRANSLATORS:" \
    --package-name="Just-Some-Bots/MusicBot" \
    --package-version="${MB_Version}" \
    --keyword="_L" \
    --keyword="_Ln" \
    --keyword="_X" \
    --keyword="debug" \
    --keyword="info" \
    --keyword="warning" \
    --keyword="error" \
    --keyword="critical" \
    --keyword="exception" \
    --keyword="everything" \
    --keyword="voicedebug" \
    --keyword="ffmpeg" \
    --keyword="noise" \
    --keyword="MusicbotException" \
    --keyword="CommandError" \
    --keyword="ExtractionError" \
    --keyword="InvalidDataError" \
    --keyword="WrongEntryTypeError" \
    --keyword="FFmpegError" \
    --keyword="FFmpegWarning" \
    --keyword="SpotifyError" \
    --keyword="PermissionsError" \
    --keyword="HelpfulError" \
    --keyword="HelpfulWarning" \
    --output="./i18n/musicbot_logs.po" \
    ./run.py \
    ./musicbot/*.py

echo "Discord domain..."
xgettext -v -F -k --language=Python --no-wrap \
    --add-comments="TRANSLATORS:" \
    --package-name="Just-Some-Bots/MusicBot" \
    --package-version="${MB_Version}" \
    --keyword="_D" \
    --keyword="_Dn" \
    --keyword="_Dd" \
    --keyword="_X" \
    --keyword="MusicbotException" \
    --keyword="CommandError" \
    --keyword="ExtractionError" \
    --keyword="InvalidDataError" \
    --keyword="WrongEntryTypeError" \
    --keyword="FFmpegError" \
    --keyword="FFmpegWarning" \
    --keyword="SpotifyError" \
    --keyword="PermissionsError" \
    --keyword="HelpfulError" \
    --keyword="HelpfulWarning" \
    --output="./i18n/musicbot_messages.po" \
    ./musicbot/*.py

echo "Done."
echo ""
