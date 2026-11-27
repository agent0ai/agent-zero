# Desktop and Tuxee updates

Desktop embeds the standard [Tuxee](https://github.com/agent0ai/tuxee) release
behind Agent Zero's authenticated `/desktop/tuxee/` route. Tuxee's About dialog
and `tuxee version` show its actual release version. Linux login, permissions,
CSRF protection and Tuxee's updater remain upstream behavior.

Update through Tuxee's About dialog, or run `tuxee update` as an administrator.
The About action restarts Tuxee automatically; the CLI installs the binary and
prints restart guidance. For the A0-managed instance, restart with:

```sh
tuxee restart --state /a0/usr/plugins/_desktop/tuxee
```

Adjust `/a0` to the checkout path for other installations.

Managed Docker instances sign in automatically using the root password generated
at startup, or an explicitly configured `ROOT_PASSWORD`; no environment variables
are required. Closing and reopening a Desktop tab, canvas or window reloads it
and renews login, including after an explicit logout. While the view stays open,
logging out leaves the Linux login form available for switching users. A valid
manual Linux session is preserved on reopening. Other installations use normal
Linux login. Tuxee preserves its retained terminals and staged editor drafts
across its normal restart.

`build/version.txt` sets the minimum supported official release. Image builds
and source-only setup select the latest official stable release at or above
that minimum and verify its published checksum and version; they never
build a privately patched Tuxee executable. Source updates refresh native
support when its recipe changes and preserve newer independently updated Tuxee
binaries. State remains under `usr/plugins/_desktop/tuxee` and Linux user homes.

A0 supplies the VNC and audio dependencies as a native Tuxee deployment. These
run in the outer environment because Desktop launches local Linux applications;
Browser also mounts the shared bundles in its separate guest. Audio is built
on Debian 12 to support that guest. Tuxee's official Docker-only startup
migrations do not run here; required system changes belong in A0's owning
recipe or [release hooks](../../docker/run/update/README.md#updating-tuxee).

The minimum is `v1.4.0`, which must include upstream commit
`6e25f6b608aa45293e5150f5998ae43461a73eb2` (proxy-path support). A first compatible
release of `v1.4.1` or later works without changing this code. Until a compatible
stable release is published, setup fails explicitly and retains the working
binary. Verify the actual published assets before shipping an A0 image.
