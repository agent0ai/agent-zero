# Import the official Node runtime and its bundled npm without Debian's large
# unbundled npm dependency tree.
FROM node:22-trixie-slim AS node-runtime

# Build the small PRoot CoW runtime separately; retain only its binary/library.
FROM debian:trixie-slim AS sandbox-tools
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl python3 build-essential pkg-config libtalloc-dev skopeo umoci \
    && rm -rf /var/lib/apt/lists/*
COPY fs/ins/proot /recipe
RUN sh /recipe/build.sh /usr/local/bin/a0-proot

# Use the official Python image and install packages into its global runtime.
FROM python:3.12-slim-trixie AS runtime

ARG DEBIAN_FRONTEND=noninteractive
ENV UV_SYSTEM_PYTHON=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
COPY --from=node-runtime /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=sandbox-tools /usr/local/bin/a0-proot /usr/local/bin/a0-proot
# Skopeo uses registry configuration and shared libraries, not Debian's CNI stack.
COPY --from=sandbox-tools /usr/bin/skopeo /usr/bin/umoci /usr/bin/
COPY --from=sandbox-tools /etc/containers/ /etc/containers/
COPY --from=sandbox-tools /usr/share/containers/ /usr/share/containers/
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx


ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=UTC

# Copy contents of the project to /
COPY ./fs/ /

# Cache OS dependencies separately from shared Python tooling.
RUN bash /ins/install_base_packages.sh && bash /ins/configure_ssh.sh
RUN bash /ins/install_python.sh

# Keep container running infinitely
CMD ["tail", "-f", "/dev/null"]
