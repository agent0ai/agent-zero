#!/bin/sh
# Build the pinned Tuxee sources and their minimal VNC runtime in a disposable builder.
set -eu
recipe=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
output=$(realpath -m "$1")
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl build-essential cmake ninja-build pkg-config autoconf automake libtool patch xutils-dev xfonts-utils xz-utils musl-tools \
    x11-xserver-utils xdotool x11-xkb-utils xkb-data libjpeg62-turbo-dev zlib1g-dev libx11-dev libxext-dev libxdamage-dev libxfixes-dev libxrandr-dev libxtst-dev \
    libxfont-dev xtrans-dev x11proto-dev libpixman-1-dev libxshmfence-dev libxkbfile-dev libfontenc-dev libpam0g-dev libunwind-dev nettle-dev
if ! command -v node >/dev/null; then apt-get install -y --no-install-recommends nodejs npm; fi
arch=$(dpkg --print-architecture)
case "$arch" in
    amd64) checksum=ccfe7ae822d2c2f41f4fe7c956199967a4dac22d0ee0d2b2bfdb440aab3b20c5 ;;
    arm64) checksum=3f4227ce7b206a513e794f1393adb473a07b46e94d18bd15d1c684bbb7319797 ;;
    *) echo 'Tuxee supports amd64 and arm64' >&2; exit 1 ;;
esac
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
cd "$build"
curl -fsSL --retry 3 "https://go.dev/dl/go1.26.10.linux-$arch.tar.gz" -o go.tar.gz
printf '%s  go.tar.gz\n' "$checksum" | sha256sum -c -
tar -xzf go.tar.gz
export PATH="$build/go/bin:$PATH"
curl -fsSL --retry 3 https://codeload.github.com/agent0ai/tuxee/tar.gz/a7e2061abce616b62951cb132e39d34d25bed3a3 -o source.tar.gz
printf '%s\n' '3aed79ded834bc57eb16b31946e149c73374d19ddc4eb5c1ee17e447ebe0fcd9  source.tar.gz' | sha256sum -c -
tar -xzf source.tar.gz
cd tuxee-*
patch -p1 < "$recipe/subpath.patch"
npm ci
npm run build
# Bookworm's musl driver ignores -static-pie; select its relocation CRT explicitly.
musl_lib=$(dirname "$(dpkg -L musl-dev | sed -n '/\/rcrt1.o$/p')")
make -C internal/keeper/native CC="musl-gcc -static -nostartfiles $musl_lib/rcrt1.o $musl_lib/crti.o $musl_lib/crtn.o -Wl,-pie,--no-dynamic-linker"
readelf -h internal/keeper/keeper.bin | grep -q 'Type:.*DYN'
if readelf -l internal/keeper/keeper.bin | grep -q INTERP; then
    echo 'Keeper must be a static PIE without a runtime loader' >&2; exit 1
fi
mkdir -p "$output/usr/local/lib/tuxee" "$output/usr/local/bin"
CGO_ENABLED=1 GOMAXPROCS=2 go build -trimpath -ldflags='-s -w -X main.version=0.0.0-a0' -o "$output/usr/local/lib/tuxee/tuxee" ./cmd/tuxee
ln -s ../lib/tuxee/tuxee "$output/usr/local/bin/tuxee"
sh "$recipe/gui.sh" "$output"
sh "$recipe/bundle-gui.sh" "$output"
install -D THIRD_PARTY_NOTICES.md "$output/usr/local/share/licenses/tuxee/THIRD_PARTY_NOTICES.md"
install -D LICENSE "$output/usr/local/share/licenses/tuxee/LICENSE"
find "$recipe" -type f -exec sha256sum {} \; | sed "s|$recipe/||" | sort | sha256sum | cut -d ' ' -f 1 > "$output/usr/local/lib/tuxee/a0-build-id"
