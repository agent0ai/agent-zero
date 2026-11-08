# Use the pre-built base image for A0
FROM agent-zero-base:local AS application
# FROM agent0ai/agent-zero-base:testing
# FROM agent0ai/agent-zero-base:latest

# Check if the argument is provided, else throw an error
ARG BRANCH
RUN if [ -z "$BRANCH" ]; then echo "ERROR: BRANCH is not set!" >&2; exit 1; fi
ENV BRANCH=$BRANCH

# Copy filesystem files to root
COPY ./fs/ /

# pre installation steps
RUN bash /ins/pre_install.sh $BRANCH

# Install Python dependencies from the currently cached branch snapshot.
RUN bash /ins/install_A0.sh $BRANCH

# install additional software
RUN bash /ins/install_additional.sh $BRANCH

# Refresh the branch through the cache buster, reuse installed Python packages, and
# install runtime assets once from the final source snapshot.
ARG CACHE_DATE=none
RUN echo "cache buster $CACHE_DATE" && bash /ins/install_A02.sh $BRANCH

# post installation steps
RUN bash /ins/post_install.sh $BRANCH

# Expose ports
EXPOSE 22 80 9000-9009

RUN chmod +x /exe/initialize.sh /exe/run_A0.sh /exe/trigger_self_update.sh

# shortcut: import bytecode events can deadlock startup watchers; remove after fixing their lock ordering.
ENV PYTHONDONTWRITEBYTECODE=1

# initialize runtime and switch to supervisord
CMD ["/exe/initialize.sh", "$BRANCH"]

FROM node:22-bookworm-slim AS sandbox-node
FROM python:3.13-slim-bookworm AS sandbox-rootfs
COPY --from=application /git/agent-zero/docker/sandbox/install.sh /tmp/install-sandbox.sh
RUN --mount=type=bind,from=sandbox-node,source=/usr/local,target=/node \
    sh /tmp/install-sandbox.sh && rm /tmp/install-sandbox.sh

FROM node:22-bookworm-slim AS tuxee-build
COPY --from=application /git/agent-zero/plugins/_desktop/build /recipe
RUN sh /recipe/build.sh /output

FROM application
COPY --from=tuxee-build /output/ /
ARG TARGETARCH
# Store the OCI bundle outside /a0 and usr so source/user mounts cannot hide it.
RUN --mount=type=bind,from=sandbox-rootfs,target=/sandbox \
    cd /git/agent-zero && /usr/local/bin/python -m plugins._sandboxing.helpers.builtin_image \
    --rootfs /sandbox --output /opt/agent-zero/sandbox-image --architecture "$TARGETARCH" && \
    chmod -R a+rX /opt/agent-zero/sandbox-image
