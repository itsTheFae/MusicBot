#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
cd ..

# extract all strings.
./i18n/extract.sh

# make sure target directory exists.
TargetXX="./i18n/xx/LC_MESSAGES/"
if [ ! -d "$TargetXX" ] ; then
    mkdir -p "$TargetXX"
fi

echo "Converting extracted messages..."

# populate translations with reversed strings.
python - <<'EOF'
import re
import pathlib
import polib

file1 = pathlib.Path("./i18n/musicbot_logs.po")
file2 = pathlib.Path("./i18n/musicbot_messages.po")

subs = re.compile("([a-z]+|f[0-9]+\.)(\)[a-z\._]+\()?%")

def uppo(po):
  for e in po:
    ns = e.msgid[::-1]
    mi = subs.finditer(ns)
    for m in mi:
      mt = m.group(0)
      ns = ns.replace(mt, mt[::-1])
    e.msgstr = ns

if file1.is_file():
  print("Making lang xx musicbot_logs.po/.mo")
  p1 = polib.pofile(file1)
  uppo(p1)
  p1.metadata["Language"] = "xx"
  p1.metadata["Content-Type"] = "text/plain; charset=UTF-8"
  p1.save("./i18n/xx/LC_MESSAGES/musicbot_logs.po")
  p1.save_as_mofile("./i18n/xx/LC_MESSAGES/musicbot_logs.mo")

if file2.is_file():
  print("Making lang xx musicbot_messagess.po/.mo")
  p2 = polib.pofile(file2)
  uppo(p2)
  p2.metadata["Language"] = "xx"
  p2.metadata["Content-Type"] = "text/plain; charset=UTF-8"
  p2.save("./i18n/xx/LC_MESSAGES/musicbot_messages.po")
  p2.save_as_mofile("./i18n/xx/LC_MESSAGES/musicbot_messages.mo")

EOF

echo "Done."
