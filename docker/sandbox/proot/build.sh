#!/bin/sh
set -eu
recipe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output=${1:-/usr/local/bin/a0-proot}
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
curl -fsSL --retry 3 https://codeload.github.com/proot-me/proot/tar.gz/refs/tags/v5.5.0 -o "$build/proot.tar.gz"
printf '%s\n' "287cfb27f58e100b0153006cb352268225bb9ad9d41d9b52ed56d01a22c13e6f  $build/proot.tar.gz" | sha256sum -c -
tar xf "$build/proot.tar.gz" -C "$build"
cp "$recipe/cow.c" "$recipe/overlay.c" "$recipe/patch.py" "$build/"
python3 "$build/patch.py"
make -C "$build/proot-5.5.0/src" -j2 WITHOUT_PYTHON=1
install -D -m 0755 "$build/proot-5.5.0/src/proot" "$output"
strip "$output"
