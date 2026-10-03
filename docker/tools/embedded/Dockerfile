FROM debian:bookworm-20250908-slim@sha256:df52e55e3361a81ac1bead266f3373ee55d29aa50cf0975d440c2be3483d8ed3

# Immutable archive date pins the complete dependency closure. APT still
# verifies Debian signatures and package hashes; only archive expiry is ignored.
RUN rm /etc/apt/sources.list.d/debian.sources \
    && printf '%s\n' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20250908T000000Z bookworm main' \
      'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/20250908T000000Z bookworm-security main' \
      > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      gcc-arm-none-eabi=15:12.2.rel1-1 \
      binutils-arm-none-eabi=2.40-2+18+b1 make=4.3-4.1 \
    && rm -rf /var/lib/apt/lists/*

ENV HOME=/tmp
WORKDIR /workspace
USER 0:0
CMD ["arm-none-eabi-gcc", "--version"]
