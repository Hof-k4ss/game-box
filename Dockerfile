FROM debian:bookworm-slim AS emulator-assets

ARG EMULATORJS_VERSION=4.2.3
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl p7zip-full \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /tmp/ejs /out \
    && curl -fL "https://cdn.emulatorjs.org/releases/${EMULATORJS_VERSION}.7z" -o /tmp/emulatorjs.7z \
    && 7z x /tmp/emulatorjs.7z -o/tmp/ejs >/dev/null \
    && DATA_DIR="$(find /tmp/ejs -type d -name data -print -quit)" \
    && test -n "$DATA_DIR" \
    && cp -a "$DATA_DIR" /out/data \
    && rm -rf /tmp/ejs /tmp/emulatorjs.7z

FROM nginx:1.29-alpine

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY app/ /usr/share/nginx/html/
COPY --from=emulator-assets /out/data /usr/share/nginx/html/emulator/data

RUN mkdir -p /srv/roms \
    && printf 'ok\n' > /usr/share/nginx/html/health \
    && chmod -R a+rX /usr/share/nginx/html
