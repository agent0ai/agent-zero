# syntax=docker/dockerfile:1
FROM node:22-trixie-slim AS node-runtime

FROM debian:trixie-slim AS sandbox-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git python3 build-essential pkg-config libtalloc-dev skopeo umoci \
    && rm -rf /var/lib/apt/lists/*
COPY docker/sandbox/proot /recipe
RUN --mount=type=bind,from=node-runtime,source=/usr/local/bin/node,target=/node \
    sh /recipe/build.sh /usr/local/bin/a0-proot && strip --strip-unneeded -o /usr/local/bin/node /node

FROM sandbox-tools AS source
ARG BRANCH
ARG SOURCE_COMMIT
RUN --mount=type=bind,target=/context \
    if [ -n "$BRANCH" ]; then \
        git clone --filter=blob:none --no-checkout --single-branch -b "$BRANCH" https://github.com/agent0ai/agent-zero /a0 \
        && git -C /a0 reset --hard "${SOURCE_COMMIT:-HEAD}"; \
    else \
        cp -a /context /a0; \
    fi

FROM python:3.12-slim-trixie AS python-runtime
ENV PIP_ROOT_USER_ACTION=ignore PYTHONDONTWRITEBYTECODE=1
# Newer pipx requires filelock/packaging versions incompatible with LiteLLM/LangChain.
RUN --mount=type=bind,from=source,source=/a0/requirements.txt,target=/requirements.txt \
    --mount=type=bind,from=source,source=/a0/docker/litellm-constraints.txt,target=/constraints.txt \
    --mount=type=bind,source=docker/strip_wheel_debug.py,target=/strip_wheel_debug.py \
    apt-get update && apt-get install -y --no-install-recommends binutils && rm -rf /var/lib/apt/lists/* \
    && /usr/local/bin/python -m pip install --no-cache-dir --no-compile --upgrade pip ipython pipx==1.16.7 uv \
    && uv pip install --no-cache --python /usr/local/bin/python -r /requirements.txt -c /constraints.txt \
    && python /strip_wheel_debug.py

FROM python:3.13-slim-trixie AS sandbox-rootfs
RUN --mount=type=bind,from=node-runtime,source=/usr/local,target=/node \
    --mount=type=bind,source=docker/sandbox/install.sh,target=/tmp/install-sandbox.sh \
    sh /tmp/install-sandbox.sh

FROM agent0ai/tuxee@sha256:4582d609640b6ab43772e6d4e8db5fab7bbf84351cc1fe1a7bb817aa0419a256
ENV UV_SYSTEM_PYTHON=1 PIP_ROOT_USER_ACTION=ignore \
    PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC A0_TUXEE_IMAGE=1 \
    HF_HUB_CACHE=/opt/agent-zero/hf-hub TIKTOKEN_CACHE_DIR=/opt/agent-zero/tiktoken

RUN --mount=type=bind,from=node-runtime,source=/usr/local,target=/node \
    --mount=type=bind,from=sandbox-tools,target=/tools \
    --mount=type=bind,source=docker/run/fs,target=/runtime \
    export DEBIAN_FRONTEND=noninteractive \
    && apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
        tzdata sudo git cron openssh-server systemd-standalone-sysusers util-linux iproute2 gpg libgpgme11t64 \
        libstdc++6 libatomic1 libtalloc2 libseccomp2 acl \
        libbz2-1.0 libcrypt1 libdb5.3t64 libffi8 libgdbm6t64 liblzma5 libncursesw6 \
        libreadline8t64 libsqlite3-0 libssl3t64 libtinfo6 libuuid1 libzstd1 netbase zlib1g \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone \
    && mkdir -p /run/sshd /usr/local/lib/node_modules /usr/local/lib/tuxee-gui /opt/a0-browser/tuxee-audio \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && cp /tools/usr/local/bin/node /tools/usr/local/bin/a0-proot /usr/local/bin/ \
    && cp -a /node/lib/node_modules/npm /usr/local/lib/node_modules/ \
    && cp /tools/usr/bin/skopeo /tools/usr/bin/umoci /usr/bin/ \
    && cp -a /tools/etc/containers /etc/ && cp -a /tools/usr/share/containers /usr/share/ \
    && ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && mkdir /opt/tuxee-guest-bin \
    && cp /usr/local/bin/tuxee-Xvnc /usr/local/bin/tuxee-vncpasswd \
        /usr/local/bin/tuxee-pulseaudio /usr/local/bin/tuxee-pacat /opt/tuxee-guest-bin/ \
    && cp -a /runtime/. /

ARG TARGETARCH
RUN --mount=type=bind,from=source,source=/a0,target=/source \
    --mount=type=bind,from=sandbox-rootfs,target=/sandbox \
    --mount=type=bind,from=python-runtime,source=/usr/local,target=/python \
    cp -a /python/. /usr/local/ && cp -a /source /a0 && cd /a0 \
    && /usr/local/bin/python -m helpers.local_embeddings \
    && /usr/local/bin/python -c 'from helpers.tokens import count_tokens; count_tokens("test")' \
    && /usr/local/bin/python preload.py --dockerized=true \
    && /usr/local/bin/python -X no_debug_ranges -m compileall -q -f --invalidation-mode checked-hash \
        -x '(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$)' /usr/local/lib/python3.12/site-packages /a0 \
    && /usr/local/bin/python -m plugins._sandboxing.helpers.builtin_image \
        --rootfs /sandbox --output /opt/agent-zero/sandbox-image-v4 --architecture "$TARGETARCH" \
    && chmod -R a+rX /opt/agent-zero/sandbox-image-v4

EXPOSE 22 80 9000-9009
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://127.0.0.1/api/health >/dev/null && tuxee healthcheck --config /etc/tuxee/a0.json
ENTRYPOINT ["/usr/bin/tini", "--", "/exe/tuxee-entrypoint.sh"]
CMD ["/usr/local/bin/tuxee", "serve", "--config", "/etc/tuxee/a0.json"]
