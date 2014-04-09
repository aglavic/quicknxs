#!/bin/bash
# create python files from Qt4 Designer
for fname in designer/*.ui; do
  name=${fname%.*}
  name=${name#designer/*}
  if [ "designer/$name.ui" -nt "quicknxs/$name.py" ] || [ ! -f "quicknxs/$name.py" ]; then 
    echo "$name.ui"
    ./pyuic4 --from-imports -i 2 "designer/$name.ui" -o "quicknxs/$name.py"
  fi
done
if [ "icons/icons.qrc" -nt "quicknxs/icons_rc.py" ]; then 
  echo "icons.qrc"
  pyrcc4 -py3 icons/icons.qrc -o quicknxs/icons_rc.py
fi
