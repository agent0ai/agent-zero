#!/bin/sh
# Source-update/native bootstrap; fresh Docker images compile in a throwaway stage.
set -eu
export DEBIAN_FRONTEND=noninteractive
recipe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
command -v apt-get >/dev/null || { echo 'Install the A0 PRoot build with libtalloc, libseccomp and POSIX ACL tools on this distribution.' >&2; exit 1; }
[ "$(id -u)" = 0 ] || { echo 'Run this runtime installer as root.' >&2; exit 1; }
previous_manual=$(apt-mark showmanual)
previous_installed=$(dpkg-query -W -f='${Package}\n')
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl python3 build-essential pkg-config libtalloc-dev acl libseccomp2
sh "$recipe/build.sh" /usr/local/bin/a0-proot.new
/usr/local/bin/a0-proot.new --version >/dev/null
mv /usr/local/bin/a0-proot.new /usr/local/bin/a0-proot
apt-mark auto build-essential pkg-config libtalloc-dev >/dev/null
apt-mark manual $previous_manual acl libtalloc2 libseccomp2 >/dev/null
# Remove only newly installed build dependencies, never unrelated old packages.
remove=$(apt-get -s autoremove | awk '/^Remv / {print $2}')
for package in $previous_installed; do
    remove=$(printf '%s\n' "$remove" | awk -v keep="$package" '$0 != keep')
done
if [ -n "$remove" ]; then apt-get purge -y $remove; fi
rm -rf /var/lib/apt/lists/*
