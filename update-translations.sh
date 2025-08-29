#!/bin/bash

# Script to refresh the translation files.
# Run it from the project root.

# Created by Philipp Kiemle, and has been slightly modified for Constrict.
# https://github.com/Wartybix/GNOME-Auto-Accent-Colour/blob/main/update-translations.sh

POTFILE="po/constrict.pot"

# Check for new translatable strings
xgettext --msgid-bugs-address="34974060+Wartybix@users.noreply.github.com" \
         --package-name="Constrict" \
         --package-version="1.0.1" \
         --copyright-holder="Wartybix" \
         --files-from="po/POTFILES.in" \
         --from-code=UTF-8 \
         --add-comments="TRANSLATORS:" \
         --keyword=_ \
         --keyword=C_:1c,2 \
         --output="$POTFILE"

# Refresh the po files if desired. Do this always when run in a GitHub Action.
if [ -n "$CI" ]; then
    response="y"
else
    read -p "Do you want to refresh the existing translations? [y|N] " -r response
fi

if [[ "$response" == "y" || "$response" == "Y" ]]; then
    for file in po/*.po; do
        echo "Refreshing $file..."
        msgmerge --update "$file" "$POTFILE"
    done
else
    echo "The existing translations were not refreshed."
fi
