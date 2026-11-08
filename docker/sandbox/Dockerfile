FROM node:22-bookworm-slim AS node-runtime
FROM python:3.13-slim-bookworm

ENV PIP_ROOT_USER_ACTION=ignore

COPY install.sh /tmp/install-sandbox.sh
RUN --mount=type=bind,from=node-runtime,source=/usr/local,target=/node \
    sh /tmp/install-sandbox.sh && rm /tmp/install-sandbox.sh

WORKDIR /workspace

CMD ["/bin/bash"]
