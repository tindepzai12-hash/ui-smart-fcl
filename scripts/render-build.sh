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
# Runtime images omit libraries present on the build image. Bundle the complete
# linked dependency closure, excluding glibc which belongs to the runtime OS.
mkdir -p tools/ocr/lib
LD_LIBRARY_PATH="$PWD/tools/ocr/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}" ldd tools/ocr/usr/bin/tesseract | awk '$2 == "=>" && $3 ~ /^\// { print $3 }' | while IFS= read -r library; do
  case "$(basename "$library")" in
    libc.so.*|libm.so.*|libpthread.so.*|libdl.so.*|librt.so.*|libresolv.so.*|ld-linux*) continue ;;
  esac
  cp -L "$library" tools/ocr/lib/
done
cat > tools/ocr/tesseract <<'WRAPPER'
#!/usr/bin/env bash
set -e
ocr_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export LD_LIBRARY_PATH="$ocr_root/lib:${LD_LIBRARY_PATH:-}"
export TESSDATA_PREFIX="$ocr_root/usr/share/tesseract-ocr/5/tessdata"
exec "$ocr_root/usr/bin/tesseract" "$@"
WRAPPER
chmod +x tools/ocr/tesseract
tools/ocr/tesseract --list-langs
node --test tests/cloud-gateway.test.mjs
