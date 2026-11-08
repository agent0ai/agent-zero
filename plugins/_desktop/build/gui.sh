#!/bin/sh
set -eu
output=$(realpath -m "$1")
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
cd "$build"
curl -fsSL --retry 3 https://github.com/TigerVNC/tigervnc/archive/refs/tags/v1.16.2.tar.gz -o tiger.tar.gz
curl -fsSL --retry 3 https://www.x.org/releases/individual/xserver/xorg-server-21.1.25.tar.xz -o xorg.tar.xz
printf '%s\n' \
    'b107c0c8b8a962594281690366c24186e95c2ea4a169acbc0076aa62ed01f467  tiger.tar.gz' \
    '6ad4e3c7b59a309b32c92e5c15ce1267110f9e13f1ac78da62361a628da1a0eb  xorg.tar.xz' | sha256sum -c -
tar xf tiger.tar.gz
tar xf xorg.tar.xz
tiger="$build/tigervnc-1.16.2"
cp -a xorg-server-21.1.25/. "$tiger/unix/xserver/"
cmake -S "$tiger" -B "$build/tiger-build" -G Ninja \
    -DBUILD_VIEWER=OFF -DENABLE_NLS=OFF -DENABLE_H264=OFF \
    -DENABLE_GNUTLS=OFF -DENABLE_NETTLE=OFF -DENABLE_SYSTEMD=OFF \
    -DENABLE_WAYLAND=OFF -DENABLE_SELINUX=OFF -DENABLE_PWQUALITY=OFF
cmake --build "$build/tiger-build" --parallel 2
cd "$tiger/unix/xserver"
patch -p1 < ../xserver21.patch
autoreconf -fiv
# Browser TLS/authentication belongs to Tuxee; the private X server needs no GPU stack.
./configure --prefix=/usr/local --disable-glx --disable-glamor \
    --disable-dri --disable-dri2 --disable-dri3 --disable-xorg \
    --disable-xnest --disable-xvfb --disable-xephyr --disable-kdrive \
    --disable-xwin --disable-config-udev --disable-systemd-logind \
    --disable-libdrm --without-dtrace --disable-static \
    --disable-devel-docs --disable-docs --disable-unit-tests \
    --with-default-font-path=built-ins --with-xkb-path=/usr/share/X11/xkb \
    --with-xkb-bin-directory=/usr/bin
make -j2 TIGERVNC_SRCDIR="$tiger" TIGERVNC_BUILDDIR="$build/tiger-build"
install -D -s hw/vnc/Xvnc "$output/usr/local/bin/tuxee-Xvnc"
install -D -s "$build/tiger-build/unix/vncpasswd/vncpasswd" "$output/usr/local/bin/tuxee-vncpasswd"
install -D "$tiger/LICENCE.TXT" "$output/usr/local/share/licenses/tuxee-gui/TigerVNC.txt"
install -D "$build/xorg-server-21.1.25/COPYING" "$output/usr/local/share/licenses/tuxee-gui/Xorg.txt"
if ldd "$output/usr/local/bin/tuxee-Xvnc" | grep -E 'libGL|libEGL|libgbm|LLVM|not found'; then
    echo 'Unexpected GUI runtime dependency' >&2
    exit 1
fi
