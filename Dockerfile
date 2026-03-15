FROM debian:trixie-slim

# --- Locale & timezone ---
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales tzdata \
    && sed -i -e 's/# \(en_US\.UTF-8 .*\)/\1/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8 \
    && ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
    && echo "UTC" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8 TZ=UTC

# --- Base image scripts ---
COPY ./docker/base/fs/ /
RUN bash /ins/install_base_packages1.sh
RUN bash /ins/install_base_packages2.sh
RUN bash /ins/install_base_packages3.sh
RUN bash /ins/install_base_packages4.sh
RUN bash /ins/install_python.sh
RUN bash /ins/install_searxng.sh
RUN bash /ins/configure_ssh.sh
RUN bash /ins/after_install.sh

# --- Run image scripts ---
COPY ./docker/run/fs/ /

ARG BRANCH=local
ENV BRANCH=$BRANCH

RUN bash /ins/pre_install.sh $BRANCH

# --- Python deps (cached unless requirements*.txt change) ---
COPY requirements.txt requirements2.txt /tmp/deps/
RUN bash -c '. /ins/setup_venv.sh && \
    uv pip install -r /tmp/deps/requirements.txt && \
    uv pip install -r /tmp/deps/requirements2.txt && \
    rm -rf /tmp/deps'

# --- Playwright (cached with deps layer) ---
RUN bash /ins/install_playwright.sh $BRANCH

# --- Bun (rarely changes) ---
RUN apt-get update && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"

# --- Source code (changes often, but deps already installed above) ---
COPY ./ /git/agent-zero

ARG A0_VERSION=unknown
RUN echo "$A0_VERSION" > /git/agent-zero/VERSION

# Verify deps are installed (near-instant, preload moved to runtime)
RUN bash /ins/install_A0.sh $BRANCH

RUN bash /ins/post_install.sh $BRANCH

# --- Code snapshot for persistent-volume overlay at runtime ---
RUN mkdir -p /a0 && cp -rn --no-preserve=ownership,mode /git/agent-zero/. /a0

EXPOSE 22 80 9000-9009

RUN chmod +x /exe/initialize.sh /exe/run_A0.sh /exe/run_searxng.sh /exe/run_tunnel_api.sh

CMD ["/exe/initialize.sh", "local"]
