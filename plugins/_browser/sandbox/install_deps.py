"""Patchright 1.61.2 Chromium dependencies, without Xvfb's dependency tree."""
import re
import subprocess

# Keep aligned with the pinned SDK; headful X11 additionally needs libx11-xcb1.
PACKAGES = (
    'libasound2', 'libatk-bridge2.0-0', 'libatk1.0-0', 'libatspi2.0-0', 'libcairo2',
    'libcups2', 'libdbus-1-3', 'libdrm2', 'libgbm1', 'libglib2.0-0', 'libnspr4',
    'libnss3', 'libpango-1.0-0', 'libx11-6', 'libx11-xcb1', 'libxcb1', 'libxcomposite1',
    'libxdamage1', 'libxext6', 'libxfixes3', 'libxkbcommon0', 'libxrandr2',
    'libfontconfig1', 'libfreetype6', 'fonts-noto-color-emoji', 'fonts-unifont',
    'fonts-liberation', 'fonts-ipafont-gothic', 'fonts-wqy-zenhei',
    'fonts-tlwg-loma-otf', 'fonts-freefont-ttf', 'libgtk-3-0', 'dbus-x11',
)
T64_PACKAGES = {'libasound2', 'libatk-bridge2.0-0', 'libatk1.0-0', 'libatspi2.0-0',
                'libcups2', 'libglib2.0-0', 'libgtk-3-0'}
# The old dry-run installer marked Xvfb's entire resolved closure as manual.
LEGACY_DISPLAY = {
    'xvfb', 'xserver-common', 'xauth', 'x11-common', 'x11-xkb-utils', 'xfonts-scalable',
    'xfonts-utils', 'xfonts-encodings', 'libfontenc1', 'libxfont2', 'libxkbfile1',
    'gir1.2-gtk-3.0', 'gir1.2-atk-1.0',
    'libdrm-amdgpu1', 'libdrm-intel1', 'libdrm-nouveau2', 'libdrm-radeon1',
    'libedit2', 'libelf1', 'libgl1', 'libgl1-mesa-dri', 'libglapi-mesa',
    'libglvnd0', 'libglx-mesa0', 'libglx0', 'libice6', 'libpciaccess0',
    'libsensors-config', 'libsensors5', 'libsm6', 'libunwind8',
    'libxaw7', 'libxcb-dri2-0', 'libxcb-dri3-0', 'libxcb-glx0', 'libxcb-present0',
    'libxcb-randr0', 'libxcb-sync1', 'libxcb-xfixes0', 'libxmu6', 'libxpm4',
    'libxt6', 'libxshmfence1', 'libxxf86vm1', 'libz3-4',
}


def native_packages(cache_output):
    available = set(re.findall(r'^Package: (\S+)$', cache_output, re.MULTILINE))
    return [name + 't64' if name in T64_PACKAGES and name + 't64' in available else name
            for name in PACKAGES]


def legacy_packages(inventory):
    result = []
    for line in inventory.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] != 'installed':
            continue
        name = fields[0].split(':', 1)[0]
        if name in LEGACY_DISPLAY or name == 'xpra' or name.startswith('xpra-') or re.fullmatch(r'libllvm\d+', name):
            result.append(fields[0])
    return result


def install():
    subprocess.run(['apt-get', 'update'], check=True)
    cache = subprocess.run(['apt-cache', 'show', *(name + 't64' for name in sorted(T64_PACKAGES))],
                           capture_output=True, text=True, timeout=30)
    # Request only direct runtime dependencies; apt decides their required closure.
    subprocess.run(['apt-get', 'install', '-y', '--no-install-recommends', *native_packages(cache.stdout)], check=True)
    inventory = subprocess.run(['dpkg-query', '-W', '-f=${binary:Package} ${db:Status-Status}\n'],
                               capture_output=True, text=True, check=True, timeout=30)
    legacy = legacy_packages(inventory.stdout)
    if legacy:
        # Required runtime packages above are manual; apt retains anything they need.
        subprocess.run(['apt-mark', 'auto', *legacy], check=True)
        subprocess.run(['apt-get', 'autoremove', '--purge', '-y'], check=True)


if __name__ == '__main__':
    install()
