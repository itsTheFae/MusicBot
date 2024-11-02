#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")" || { echo "failed to change directory"; exit 1; }
cd .. || { echo "failed to change directory"; exit 1; }

LogPotFile="./i18n/musicbot_logs.pot"
MsgPotFile="./i18n/musicbot_messages.pot"
OldLogPot="${LogPotFile}.old"
OldMsgPot="${MsgPotFile}.old"

# Check for existing translations or exit.
if [ ! -f "$LogPotFile" ] && [ ! -f "$MsgPotFile" ] ; then
    echo "No existing files to diff against."
    exit 0
fi

# Check for existing old files or create new ones.
HasMoved=1
if [ ! -f "$OldLogPot" ] || [ "$1" == "force" ] ; then
    mv "$LogPotFile" "$OldLogPot" || { echo "failed to rename old POT file."; exit 1; }
    HasMoved=0
fi
if [ ! -f "$OldMsgPot" ]  || [ "$1" == "force" ] ; then
    mv "$MsgPotFile" "$OldMsgPot" || { echo "failed to rename old POT file."; exit 1; }
    HasMoved=0
fi

# extract all strings.
if [ $HasMoved ] ; then
    ./i18n/extract.sh
fi

# run the diff, and grep to exclude comments.
echo "Diff for Log strings:"
diff --color=always "$OldLogPot" "$LogPotFile" | grep '"'

echo ""
echo "Diff for Discord strings:"
diff --color=always "$OldMsgPot" "$MsgPotFile" | grep '"'

echo ""
echo "Done"
echo ""

