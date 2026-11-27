#!/bin/sh
# Adapted from Tuxee 6e25f6b608aa45293e5150f5998ae43461a73eb2, MIT (LICENSE.tuxee).
set -eu
output=$(realpath -m "$1")
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
cd "$build"
curl -fsSL --retry 3 https://freedesktop.org/software/pulseaudio/releases/pulseaudio-17.0.tar.xz -o pulse.tar.xz
curl -fsSL --retry 3 https://deb.debian.org/debian/pool/main/libs/libsndfile/libsndfile_1.2.2.orig.tar.gz -o sndfile.tar.gz
printf '%s\n' \
    '053794d6671a3e397d849e478a80b82a63cb9d8ca296bd35b73317bb5ceb87b5  pulse.tar.xz' \
    'ffe12ef8add3eaca876f04087734e6e8e029350082f3251f565fa9da55b52121  sndfile.tar.gz' | sha256sum -c -
tar xf pulse.tar.xz
tar xf sndfile.tar.gz
prefix=/usr/local/lib/tuxee-audio
# Applications decode their media; the server only mixes PCM and cached sounds.
cmake -S libsndfile-1.2.2 -B sndfile-build -G Ninja \
    -DCMAKE_BUILD_TYPE=MinSizeRel -DCMAKE_INSTALL_PREFIX="$build/deps" -DCMAKE_INSTALL_LIBDIR=lib \
    -DBUILD_SHARED_LIBS=ON -DBUILD_PROGRAMS=OFF -DBUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF \
    -DENABLE_EXTERNAL_LIBS=OFF -DENABLE_MPEG=OFF -DINSTALL_MANPAGES=OFF -DENABLE_CPACK=OFF
cmake --build sndfile-build --parallel 2
cmake --install sndfile-build --strip
PKG_CONFIG_PATH="$build/deps/lib/pkgconfig" meson setup pulse-build pulseaudio-17.0 \
    --prefix="$prefix" --libdir=lib --buildtype=minsize -Dauto_features=disabled \
    -Ddatabase=simple -Dtests=false -Dman=false -Ddoxygen=false -Db_lto=true -Dstrip=true \
    -Dbashcompletiondir=no -Dzshcompletiondir=no
ninja -C pulse-build -j2
DESTDIR="$build/stage" meson install -C pulse-build --no-rebuild
runtime="$output$prefix"
mkdir -p "$runtime/bin" "$runtime/lib/pulseaudio/modules" "$output/usr/local/bin"
for name in pulseaudio pacat; do install -s "$build/stage$prefix/bin/$name" "$runtime/bin/$name"; done
cp -a "$build/stage$prefix"/lib/libpulse.so* "$runtime/lib/"
for name in libpulsecommon-17.0.so libpulsecore-17.0.so; do
    install -s "$build/stage$prefix/lib/pulseaudio/$name" "$runtime/lib/pulseaudio/$name"
done
for name in libprotocol-native.so module-native-protocol-unix.so module-null-sink.so module-remap-source.so; do
    install -s "$build/stage$prefix/lib/pulseaudio/modules/$name" "$runtime/lib/pulseaudio/modules/$name"
done
cp -a "$build/deps"/lib/libsndfile.so* "$runtime/lib/"
install -s "$(cc -print-file-name=libltdl.so)" "$runtime/lib/libltdl.so.7"
for name in pulseaudio pacat; do
    arguments=''
    if [ "$name" = pulseaudio ]; then arguments='-p "$runtime/lib/pulseaudio/modules"'; fi
    cat > "$runtime/tuxee-$name" <<EOF
#!/bin/sh
set -eu
runtime=\$(CDPATH= cd -- "\$(dirname -- "\$(readlink -f "\$0")")" && pwd)
export LD_LIBRARY_PATH="\$runtime/lib:\$runtime/lib/pulseaudio:\$runtime/lib/pulseaudio/modules"
exec "\$runtime/bin/$name" $arguments "\$@"
EOF
    chmod 0755 "$runtime/tuxee-$name"
    ln -s ../lib/tuxee-audio/tuxee-$name "$output/usr/local/bin/tuxee-$name"
done
install -D pulseaudio-17.0/LGPL "$runtime/licenses/PulseAudio.txt"
install -D libsndfile-1.2.2/COPYING "$runtime/licenses/libsndfile.txt"
install -D /usr/share/doc/libltdl7/copyright "$runtime/licenses/libltdl.txt"
LD_LIBRARY_PATH="$runtime/lib:$runtime/lib/pulseaudio:$runtime/lib/pulseaudio/modules" \
    ldd "$runtime/bin/pulseaudio" "$runtime/bin/pacat" "$runtime/lib/pulseaudio/modules/"*.so > "$build/dependencies"
if grep -E 'libFLAC|libvorbis|libopus|libmpg123|libmp3lame|libavcodec|libgstreamer|not found' "$build/dependencies"; then
    echo 'Unexpected audio runtime dependency' >&2
    exit 1
fi
if grep ' => ' "$build/dependencies" | grep -Ev '^[[:space:]]+(libpulse[^ ]*|libprotocol-native.so|libsndfile.so.1|libltdl.so.7|libcap.so.2|libm.so.6|libc.so.6) => '; then
    echo 'Unaccounted audio runtime dependency' >&2
    exit 1
fi
