#!/bin/sh
# Install an unmodified official release; never fall back to a development build.
set -eu
recipe=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
output=$(realpath -m "$1")
minimum=$(cat "$recipe/version.txt")
# Resolve once so every asset comes from the same published stable release.
latest=$(curl -fsS --retry 3 -o /dev/null -w '%{redirect_url}' https://github.com/agent0ai/tuxee/releases/latest)
case "$latest" in
    https://github.com/agent0ai/tuxee/releases/tag/*) version=${latest##*/} ;;
    *) echo 'Cannot resolve the latest official Tuxee release' >&2; exit 1 ;;
esac
if ! printf '%s\n' "$version" | grep -Eq '^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$'; then
    echo 'Expected a stable Tuxee release version' >&2; exit 1
fi
if [ "$(printf '%s\n' "$minimum" "$version" | sort -V | head -n 1)" != "$minimum" ]; then
    echo "Tuxee $minimum or newer is required; latest published release is $version" >&2; exit 1
fi
arch=$(dpkg --print-architecture)
case "$arch" in
    amd64|arm64) ;;
    *) echo 'Tuxee supports amd64 and arm64' >&2; exit 1 ;;
esac
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
cd "$build"
asset="tuxee-linux-$arch"
url="https://github.com/agent0ai/tuxee/releases/download/$version"
curl -fsSL --retry 3 "$url/checksums.txt" -o checksums.txt
curl -fsSL --retry 3 "$url/$asset" -o "$asset"
awk -v asset="$asset" '$2 == asset {print; count++} END {if (count != 1) exit 1}' checksums.txt > selected.sha256
sha256sum -c selected.sha256
chmod 0755 "$asset"
test "$(./"$asset" version)" = "Tuxee ${version#v}"
install -D "$asset" "$output/usr/local/lib/tuxee/tuxee"
# The absolute command link is created at final installation, outside the worker tar.
install -Dm644 "$recipe/LICENSE.tuxee" "$output/usr/local/share/licenses/tuxee/LICENSE"
