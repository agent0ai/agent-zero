# Use the latest slim version of Kali Linux
# hadolint ignore=DL3006
FROM kalilinux/kali-rolling

# Pin Kali mirror to kali.download (Cloudflare CDN) for reliable Docker builds.
# The default http.kali.org redirector can route to unreliable mirrors.
# Uses http:// because the base image lacks ca-certificates for TLS verification.
# APT verifies package integrity via GPG signatures, not TLS.
# See: https://www.kali.org/docs/community/kali-linux-mirrors/
RUN echo "deb http://kali.download/kali kali-rolling main non-free non-free-firmware contrib" > /etc/apt/sources.list

# Set locale to en_US.UTF-8 and timezone to UTC
# hadolint ignore=DL3009
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends locales tzdata
RUN sed -i -e 's/# \(en_US\.UTF-8 .*\)/\1/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime
RUN echo "UTC" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV TZ=UTC

# Copy contents of the project to /
COPY ./fs/ /

# install packages software (split for better cache management)
RUN bash /ins/install_base_packages1.sh
RUN bash /ins/install_base_packages2.sh
RUN bash /ins/install_base_packages3.sh
RUN bash /ins/install_base_packages4.sh

# install python after packages to ensure version overriding
RUN bash /ins/install_python.sh

# install searxng
RUN bash /ins/install_searxng.sh

# configure ssh
RUN bash /ins/configure_ssh.sh

# after install
RUN bash /ins/after_install.sh

# Keep container running infinitely
CMD ["tail", "-f", "/dev/null"]
