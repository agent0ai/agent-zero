# Python and Node sandbox image

This image provides Python 3.13, pip and IPython in the global Python environment,
plus Node.js 22, npm and npx. Both official runtime images use Debian Bookworm.
It contains no Agent Zero framework dependencies or user data.

`agent-zero-sandbox:1` is the default for new sandboxes. Both Agent Zero Docker
builds include an OCI bundle at `/opt/agent-zero/sandbox-image`, outside the
source and user-data mounts. No registry publication or manual import is needed.
The first sandbox creation unpacks that bundle into the normal disk cache,
without network access. Later starts reuse the cached image and private files.

If the bundle is absent or damaged (including native installs and older Docker
images), the sandbox manager builds it on first use in a temporary gVisor
sandbox. It pulls the official Python and Node images and runs `install.sh`,
the same recipe used by Docker builds. This needs internet access and working
`runsc`, `skopeo` and `umoci`; host Python packages remain untouched. Builds are
serialized and cached, and never run as part of ordinary WebUI startup.
Existing sandboxes retain their pinned digest and explicit image settings are
preserved. Rebuilding cannot substitute a different digest for a lost pinned
base; preserve the image cache with your sandbox backups.

An optional standalone image can be built from the repository root:

```sh
docker build -t agent-zero-sandbox:local docker/sandbox
docker run --rm agent-zero-sandbox:local python -c 'import sys; assert sys.prefix == sys.base_prefix'
docker run --rm agent-zero-sandbox:local node --version
docker run --rm agent-zero-sandbox:local npm --version
```

`python -m pip install ...` installs globally inside the sandbox. Node projects
can use `npm install` normally. Each sandbox owns its writable filesystem, so
these installations do not modify the cached base image or other sandboxes.

To try a separately modified local image, import it into an Agent Zero container
(replace `YOUR_A0_CONTAINER`):

```sh
docker save -o /tmp/agent-zero-sandbox.tar agent-zero-sandbox:local
docker cp /tmp/agent-zero-sandbox.tar YOUR_A0_CONTAINER:/tmp/agent-zero-sandbox.tar
docker exec -w /a0 YOUR_A0_CONTAINER /usr/local/bin/python -m helpers.sandbox \
  import-image /tmp/agent-zero-sandbox.tar agent-zero-sandbox:local
```

Set **Sandboxing → Default image** to `agent-zero-sandbox:local`. Native
installations can run the same Python command directly with the archive path.
The loader uses Skopeo and umoci; Agent Zero never needs a Docker socket.
The imported image stays in the normal disk cache and remains protected while
any sandbox references it. Reimport after manually deleting the cached image
or after unused-image expiry. Importing a rebuilt image under the same reference
changes the base for new sandboxes; existing sandboxes retain their pinned image.

Other custom images can also be published to a registry and selected in
Sandboxing settings. The built-in default needs no separate registry image.
