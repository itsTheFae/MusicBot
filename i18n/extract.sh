#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
cd ..

MB_Version="$(git describe --tags --always)"

echo "Extracting strings for translation from MusicBot $MB_Version"

echo "Log domain..."
xgettext -v -F --language=Python --no-wrap \
    --add-comments="TRANSLATORS:" \
    --package-name="Just-Some-Bots/MusicBot" \
    --package-version="${MB_Version}" \
    --keyword="_L" \
    --keyword="_Ln" \
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
    --output="./i18n/musicbot_messages.po" \
    ./musicbot/*.py

echo "Done."
echo ""
