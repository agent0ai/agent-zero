#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
mkdir -p /usr/local/share/fonts
ln -sfn /support /app/helpers
ln -sfn /plugin /app/plugins/_browser

apt_updated=false
install_packages() {
    if states=$(dpkg-query -W -f='${db:Status-Status}\n' "$@" 2>/dev/null) &&
        ! printf '%s\n' "$states" | grep -qvx installed; then
        return
    fi
    if [ "$apt_updated" = false ]; then
        apt-get update
        apt_updated=true
    fi
    apt-get install -y --no-install-recommends "$@"
}

python /worker/progress.py viewer 'Preparing browser display and audio'
. /etc/os-release
display_packages=
if [ "${VERSION_CODENAME:-}" = trixie ] && [ -x /opt/tuxee-guest-bin/tuxee-Xvnc ]; then
    display_packages='libnettle8t64 libunwind8 libjpeg62-turbo libpam0g libpixman-1-0 libxfont2 x11-xserver-utils xdotool x11-xkb-utils xkb-data'
    mkdir -p /opt/tuxee-gui/bin
    [ -e /opt/tuxee-gui/xkb ] || ln -sfn /usr/share/X11/xkb /opt/tuxee-gui/xkb
    [ -e /opt/tuxee-gui/bin/xkbcomp ] || ln -sfn /usr/bin/xkbcomp /opt/tuxee-gui/bin/xkbcomp
    [ -e /usr/local/lib/tuxee-audio ] || ln -s /opt/tuxee-guest-audio /usr/local/lib/tuxee-audio
    for tool in tuxee-Xvnc tuxee-vncpasswd tuxee-pulseaudio tuxee-pacat; do
        ln -sfn "/opt/tuxee-guest-bin/$tool" "/usr/local/bin/$tool"
    done
else
    if [ ! -x /opt/tuxee-gui/bin/tuxee-Xvnc ]; then
        python /worker/progress.py viewer 'Building minimal Tuxee display server (first use)'
        previous_manual=$(apt-mark showmanual)
        build_packages='ca-certificates curl build-essential cmake ninja-build pkg-config autoconf automake libtool patch xutils-dev xfonts-utils xz-utils x11-xserver-utils xdotool x11-xkb-utils xkb-data libjpeg62-turbo-dev zlib1g-dev libx11-dev libxext-dev libxdamage-dev libxfixes-dev libxrandr-dev libxtst-dev libxfont-dev xtrans-dev x11proto-dev libpixman-1-dev libxshmfence-dev libxkbfile-dev libfontenc-dev libpam0g-dev libunwind-dev nettle-dev'
        install_packages $build_packages
        sh /support/build-gui.sh /tmp/a0-gui
        sh /support/bundle-gui.sh /tmp/a0-gui
        mkdir -p /opt/tuxee-gui
        cp -a /tmp/a0-gui/usr/local/lib/tuxee-gui/. /opt/tuxee-gui/
        rm -rf /tmp/a0-gui
        apt-mark auto $build_packages > /dev/null
        apt-mark manual $previous_manual > /dev/null
        apt-get autoremove --purge -y
    fi
    for tool in /opt/tuxee-gui/bin/*; do ln -sfn "$tool" "/usr/local/bin/$(basename "$tool")"; done
    if [ ! -x /usr/local/lib/tuxee-audio/tuxee-pulseaudio ]; then
        python /worker/progress.py viewer 'Building minimal Tuxee audio runtime (first use)'
        previous_manual=$(apt-mark showmanual)
        build_packages='ca-certificates curl build-essential cmake ninja-build meson pkg-config libltdl-dev libcap-dev'
        install_packages $build_packages libcap2
        sh /support/build-audio.sh /tmp/a0-audio
        cp -a /tmp/a0-audio/usr/local/. /usr/local/
        rm -rf /tmp/a0-audio
        apt-mark auto $build_packages > /dev/null
        apt-mark manual $previous_manual libcap2 > /dev/null
        apt-get autoremove --purge -y
    fi
    for tool in pulseaudio pacat; do ln -sfn "/usr/local/lib/tuxee-audio/tuxee-$tool" "/usr/local/bin/tuxee-$tool"; done
    # The bundled X server locates xkbcomp through this compiled-in path.
    [ -e /usr/bin/xkbcomp ] || ln -s /opt/tuxee-gui/bin/xkbcomp /usr/bin/xkbcomp
fi

python /worker/progress.py chromium 'Preparing Chromium and fonts'
browser=/opt/runtime/bin/a0-chromium
browser_package=
cached=
if [ ! -x "$browser" ]; then
    # Earlier v3 guests kept their full browser here without putting it on PATH.
    for binary in /opt/browsers/chromium-*/chrome-*/chrome; do
        [ -f "${binary%/*}/../INSTALLATION_COMPLETE" ] && [ -f "$binary" ] && [ -x "$binary" ] || continue
        if [ -n "$cached" ]; then
            echo "Multiple installed Chromium builds found. Link the desired executable to $browser and retry." >&2
            exit 1
        fi
        cached=$binary
    done
    if [ -z "$cached" ] && ! command -v chromium >/dev/null; then
        browser_package=chromium
    fi
fi

# Trixie renamed GTK's package while retaining the same library and virtual package.
gtk=libgtk-3-0
if [ "$(dpkg-query -W -f='${db:Status-Status}' libgtk-3-0t64 2>/dev/null)" = installed ]; then
    gtk=libgtk-3-0t64
fi
install_packages $browser_package $display_packages "$gtk" libcap2 dbus-x11 libx11-xcb1 \
    fonts-noto-color-emoji fonts-unifont fonts-liberation fonts-ipafont-gothic \
    fonts-wqy-zenhei fonts-tlwg-loma-otf fonts-freefont-ttf
if [ ! -x "$browser" ]; then
    chromium=${cached:-$(command -v chromium)}
    mkdir -p /opt/runtime/bin
    ln -sfn "$chromium" "$browser"
fi
# Cover both adopted Chrome for Testing and Debian Chromium in the guest.
for policy_root in /etc/opt/chrome_for_testing /etc/chromium; do
    install -D -m 0644 /plugin/sandbox/install-browser-policy.json "$policy_root/policies/managed/agent-zero-browser.json"
done
"$browser" --version
if [ "$apt_updated" = true ]; then rm -rf /var/lib/apt/lists/*; fi
