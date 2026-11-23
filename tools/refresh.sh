#!/bin/sh
# Refreshes the showroom: retakes the live sites' screenshots, rebuilds the page, then retakes the
# hub's own design thumbnails and social card from the rebuilt page. Run from anywhere.
set -u
cd "$(dirname "$0")/.."
node tools/take-shots.js; shots=$?
python3 tools/thumbs.py
python3 tools/build-building.py || echo "building: register not read, old list kept"
python3 tools/build-showroom.py || exit 1
python3 -m http.server 8766 -d site >/dev/null 2>&1 & srv=$!
sleep 1; node tools/hub-shots.js; kill $srv
python3 tools/build-showroom.py >/dev/null
exit $shots
