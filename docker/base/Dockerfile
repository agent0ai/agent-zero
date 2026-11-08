# Import the official Node runtime and its bundled npm without Debian's large
# unbundled npm dependency tree.
FROM node:22-trixie-slim AS node-runtime

# Install the signed gVisor package and OCI tools outside the final image. Current gVisor
# releases split the Sentry from runsc, while the other packaged executables
# support containerd, remote checkpoints, or optional metrics.
FROM debian:trixie-slim AS gvisor-package

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://gvisor.dev/archive.key \
        | gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" \
        > /etc/apt/sources.list.d/gvisor.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends runsc skopeo umoci \
    && test -x /usr/bin/runsc \
    && test -x /usr/bin/gvisor-bin/gvisor_sentry \
    && rm -rf /var/lib/apt/lists/*

# Use the official Python image and install packages into its global runtime.
FROM python:3.12-slim-trixie AS runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV UV_SYSTEM_PYTHON=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node-runtime /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=gvisor-package /usr/bin/runsc /usr/bin/runsc
COPY --from=gvisor-package /usr/bin/gvisor-bin/gvisor_sentry /usr/bin/gvisor-bin/gvisor_sentry
# Skopeo uses registry configuration and shared libraries, not Debian's CNI stack.
COPY --from=gvisor-package /usr/bin/skopeo /usr/bin/umoci /usr/bin/
COPY --from=gvisor-package /etc/containers/ /etc/containers/
COPY --from=gvisor-package /usr/share/containers/ /usr/share/containers/
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx


# Use Debian's built-in UTF-8 locale and configure the UTC timezone.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata \
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
    && echo "UTC" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=UTC

# Copy contents of the project to /
COPY ./fs/ /

# install packages software (split for better cache management)
RUN bash /ins/install_base_packages1.sh
RUN bash /ins/install_base_packages2.sh
RUN bash /ins/install_base_packages3.sh
RUN bash /ins/install_base_packages4.sh

# install shared Python tooling into the image's global environment
RUN bash /ins/install_python.sh

# configure ssh
RUN bash /ins/configure_ssh.sh

# after install
RUN bash /ins/after_install.sh

# Current runsc also needs these sandbox-process helpers.
COPY --from=gvisor-package /usr/bin/gvisor-bin/gvisor-sentry-prewarmer /usr/bin/gvisor-bin/gvisor-sentry-prewarmer
COPY --from=gvisor-package /usr/bin/gvisor-bin/gvisor-proc-umounter /usr/bin/gvisor-bin/gvisor-proc-umounter
COPY --from=gvisor-package /usr/bin/gvisor-bin/runsc-fd-parking /usr/bin/gvisor-bin/runsc-fd-parking

# Keep container running infinitely
CMD ["tail", "-f", "/dev/null"]
