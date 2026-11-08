#!/bin/bash
set -e

if ! command -v apt-get >/dev/null 2>&1; then
  echo "apt-get unavailable; skipping LibreOffice install"
  exit 0
fi

XPRA_VERSION="6.5.2-r0-1"
arch="$(dpkg --print-architecture)"

XPRA_HTML5_VERSION="19-r1-1"
if [ "$arch" = "arm64" ]; then
  XPRA_HTML5_VERSION="21-r1-1"
fi

LIBREOFFICE_PACKAGES=(
  "libreoffice-core"
  "libreoffice-writer"
  "libreoffice-calc"
  "libreoffice-impress"
  "libreoffice-gtk3"
  "python3-uno"
)
XPRA_PACKAGES=(
  "xpra-common=$XPRA_VERSION"
  "xpra-server=$XPRA_VERSION"
  "xpra-client=$XPRA_VERSION"
  "xpra-client-gtk3=$XPRA_VERSION"
  "xpra-x11=$XPRA_VERSION"
  "xpra-html5=$XPRA_HTML5_VERSION"
)

# Match the official Debian base; do not cross-upgrade it from a rolling snapshot.
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ca-certificates wget libsndfile1
wget -O /usr/share/keyrings/xpra.asc https://xpra.org/xpra.asc
cat >/etc/apt/sources.list.d/xpra.sources <<EOF
Types: deb
URIs: https://xpra.org
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/xpra.asc
Architectures: $arch
EOF
bash /git/agent-zero/plugins/_desktop/helpers/refresh_xpra_index.sh /etc/apt/sources.list.d/xpra.sources
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --allow-downgrades \
  gir1.2-atk-1.0 \
  gir1.2-gtk-3.0 \
  "${LIBREOFFICE_PACKAGES[@]}" \
  "${XPRA_PACKAGES[@]}" \
  xfce4-session \
  xfwm4 \
  xfce4-panel \
  xfdesktop4 \
  xfce4-settings \
  thunar \
  gvfs \
  libglib2.0-bin \
  xfce4-terminal \
  x11-xserver-utils \
  x11-utils \
  x11-apps \
  xdotool \
  xclip \
  xauth \
  xvfb \
  dbus-x11 \
  fonts-dejavu \
  fonts-liberation \
  fonts-crosextra-caladea \
  fonts-crosextra-carlito \
  fonts-noto-core \
  fonts-noto-cjk \
  fonts-noto-color-emoji

rm -rf /var/lib/apt/lists/*
