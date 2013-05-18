#!/bin/bash
# create python files from Qt4 Designer
for fname in designer/*.ui; do
  name=${fname%.*}
  name=${name#designer/*}
  if [ "designer/$name.ui" -nt "quick_nxs/$name.py" ] || [ ! -f "quick_nxs/$name.py" ]; then 
    echo "$name.ui"
    ./pyuic4 --from-imports -i 2 "designer/$name.ui" -o "quick_nxs/$name.py"
  fi
done
if [ "icons/icons.qrc" -nt "quick_nxs/icons_rc.py" ]; then 
  echo "icons.qrc"
  pyrcc4 -py3 icons/icons.qrc -o quick_nxs/icons_rc.py
fi
