rm -r QuickNXS_Users_Manual
latex2html -split 3 -antialias -show_section_numbers -address 0 -html_version=4.0 -info 0 QuickNXS_Users_Manual.tex
cp QuickNXS_Users_Manual/* ../../quicknxs/htmldoc/
