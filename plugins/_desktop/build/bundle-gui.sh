#!/bin/sh
# Package only the native display tools and their loader/library closure.
set -eu
output=$(realpath -m "$1")
bundle="$output/usr/local/lib/tuxee-gui"
mkdir -p "$bundle/bin" "$bundle/lib" "$bundle/libexec" "$bundle/licenses"
copy_license() {
    package=$(dpkg-query -S "$1" 2>/dev/null | sed -n '1s/: \/.*//p' || true)
    if [ -z "$package" ]; then
        package=$(dpkg-query -S "$(readlink -f "$1")" 2>/dev/null | sed -n '1s/: \/.*//p' || true)
    fi
    notice="/usr/share/doc/${package%%:*}/copyright"
    if [ -n "$package" ] && [ -f "$notice" ]; then cp -L "$notice" "$bundle/licenses/$package"; fi
}
for tool in tuxee-Xvnc tuxee-vncpasswd xrandr xdotool setxkbmap xkbcomp; do
    binary="$output/usr/local/bin/$tool"
    if [ ! -x "$binary" ]; then binary=$(command -v "$tool"); fi
    cp "$binary" "$bundle/libexec/$tool"
    copy_license "$binary"
    ldd "$binary" | awk '/=> \/|^[[:space:]]*\// {for (i=1; i<=NF; i++) if ($i ~ /^\//) print $i}' | while read -r library; do
        cp -L "$library" "$bundle/lib/$(basename "$library")"
        copy_license "$library"
    done
    loader=$(ldd "$binary" | sed -n 's|^[[:space:]]*\(/[^ ]*/ld-linux[^ ]*\).*|\1|p')
    test -n "$loader"
    cp -L "$loader" "$bundle/lib/$(basename "$loader")"
    cat > "$bundle/bin/$tool" <<SCRIPT
#!/bin/sh
base=\$(dirname "\$(dirname "\$(readlink -f "\$0")")")
exec "\$base/lib/$(basename "$loader")" --library-path "\$base/lib" "\$base/libexec/$tool" "\$@"
SCRIPT
    chmod 755 "$bundle/bin/$tool"
done
cp -a /usr/share/X11/xkb "$bundle/xkb"
copy_license /usr/share/X11/xkb/rules/evdev
if [ -d "$output/usr/local/share/licenses/tuxee-gui" ]; then
    cp -a "$output/usr/local/share/licenses/tuxee-gui/." "$bundle/licenses/"
fi
cp -a /usr/share/common-licenses "$bundle/licenses/"
