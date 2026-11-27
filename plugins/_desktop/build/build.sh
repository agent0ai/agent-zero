#!/bin/sh
# Fetch official Tuxee and build its shared native support in a disposable builder.
set -eu
recipe=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
output=$(realpath -m "$1")
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl build-essential cmake ninja-build meson libltdl-dev libcap-dev pkg-config autoconf automake libtool patch xutils-dev xfonts-utils xz-utils \
    x11-xserver-utils xdotool x11-xkb-utils xkb-data libjpeg62-turbo-dev zlib1g-dev libx11-dev libxext-dev libxdamage-dev libxfixes-dev libxrandr-dev libxtst-dev \
    libxfont-dev xtrans-dev x11proto-dev libpixman-1-dev libxshmfence-dev libxkbfile-dev libfontenc-dev libpam0g-dev libunwind-dev nettle-dev
sh "$recipe/release.sh" "$output"
sh "$recipe/gui.sh" "$output"
sh "$recipe/bundle-gui.sh" "$output"
sh "$recipe/audio.sh" "$output"
find "$recipe" -type f -exec sha256sum {} \; | sed "s|$recipe/||" | sort | sha256sum | cut -d ' ' -f 1 > "$output/usr/local/lib/tuxee/a0-build-id"
