#!/usr/bin/env bash
set -euo pipefail
npm ci --include=dev
npm run build
python3 -m pip install --disable-pip-version-check --no-cache-dir --target vendor -r requirements-cloud.txt
# Native Node has Python but no Tesseract. Extract Debian packages without root.
mkdir -p tools/debs tools/ocr tools/apt/lists/partial tools/apt/cache/archives/partial
apt_options=(-o "Dir::State::lists=$PWD/tools/apt/lists" -o "Dir::Cache=$PWD/tools/apt/cache")
apt-get "${apt_options[@]}" update
cd tools/debs
apt-get "${apt_options[@]}" download tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie libtesseract5 liblept5
for package in ./*.deb; do dpkg-deb -x "$package" ../ocr; done
cd ../..
LD_LIBRARY_PATH="$PWD/tools/ocr/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}" TESSDATA_PREFIX="$PWD/tools/ocr/usr/share/tesseract-ocr/5/tessdata" tools/ocr/usr/bin/tesseract --list-langs
node --test tests/cloud-gateway.test.mjs
