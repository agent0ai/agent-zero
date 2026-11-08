#!/bin/sh
set -eu
python /worker/progress.py python 'Preparing image Python environment'
base_python=$(command -v python)
base_interpreter=$("$base_python" -c 'import os, sys; print(os.path.realpath(sys.executable))')
if [ "$(readlink -f /opt/runtime/bin/python 2>/dev/null || true)" != "$base_interpreter" ]; then
    "$base_python" -m venv --without-pip --symlinks --clear /opt/runtime
fi
export PATH=/opt/runtime/bin:$PATH
mkdir -p /usr/local/share/fonts
ln -sfn /support /app/helpers
ln -sfn /plugin /app/plugins/_browser
export DEBIAN_FRONTEND=noninteractive
python /worker/progress.py viewer 'Preparing shared Tuxee browser viewer'
# Retire the previous viewer repository before refreshing package lists.
rm -f /etc/apt/sources.list.d/xpra.list /var/lib/apt/lists/xpra.org_*
if [ ! -x /opt/tuxee-gui/bin/tuxee-Xvnc ]; then
    python /worker/progress.py viewer 'Building minimal Tuxee display server (first use)'
    previous_manual=$(apt-mark showmanual)
    build_packages='ca-certificates curl build-essential cmake ninja-build pkg-config autoconf automake libtool patch xutils-dev xfonts-utils xz-utils x11-xserver-utils xdotool x11-xkb-utils xkb-data libjpeg62-turbo-dev zlib1g-dev libx11-dev libxext-dev libxdamage-dev libxfixes-dev libxrandr-dev libxtst-dev libxfont-dev xtrans-dev x11proto-dev libpixman-1-dev libxshmfence-dev libxkbfile-dev libfontenc-dev libunwind-dev nettle-dev'
    apt-get update
    apt-get install -y --no-install-recommends $build_packages
    sh /support/build-gui.sh /tmp/a0-gui
    sh /support/bundle-gui.sh /tmp/a0-gui
    mv /tmp/a0-gui/usr/local/lib/tuxee-gui /opt/tuxee-gui
    rm -rf /tmp/a0-gui
    apt-mark auto $build_packages > /dev/null
    apt-mark manual $previous_manual > /dev/null
    apt-get autoremove --purge -y
fi
for tool in /opt/tuxee-gui/bin/*; do ln -sfn "$tool" "/usr/local/bin/$(basename "$tool")"; done
python /worker/progress.py driver 'Installing browser driver'
"$base_python" -m pip --python /opt/runtime install --no-cache-dir --disable-pip-version-check -c /worker/constraints.txt -r /plugin/sandbox/requirements.txt
# Patchright supports the image's Node; keep its bundled binary for older/custom images.
if command -v node >/dev/null && node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
    driver=$(python -c 'from pathlib import Path; import patchright; print(Path(patchright.__file__).parent / "driver/node")')
    ln -sfn "$(command -v node)" "$driver"
fi
export PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
python /worker/progress.py chromium_dependencies 'Installing Chromium dependencies'
python /plugin/sandbox/install_deps.py
python /worker/progress.py chromium 'Downloading Chromium'
python -m patchright install chromium --no-shell
if "$base_python" -c 'import importlib.util; exit(importlib.util.find_spec("uv") is None)'; then
    "$base_python" -m pip uninstall -y uv
fi
case "$base_interpreter" in
    /root/.local/share/uv/python/*) ;; # A custom image may use managed Python itself.
    *) rm -rf /root/.local/share/uv/python ;;
esac
rm -rf /root/.cache/uv
rm -rf /var/lib/apt/lists/*
# Xvnc's compiled helper path stays private without replacing a package-owned directory.
if [ ! -e /usr/bin/xkbcomp ]; then ln -s /opt/tuxee-gui/bin/xkbcomp /usr/bin/xkbcomp; fi
