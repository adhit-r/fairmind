FROM node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# PUBLIC_* values are inlined at build time
ARG PUBLIC_APP_URL
ARG PUBLIC_DEMO_URL
ARG PUBLIC_DEMO_EMAIL
ARG PUBLIC_DEMO_PASSWORD
ARG PUBLIC_POSTHOG_KEY
ARG PUBLIC_POSTHOG_HOST
RUN npm run build

FROM caddy:2.11-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0
COPY --from=build /app/dist /srv
# Run as a non-root user. The Caddy binary carries cap_net_bind_service, so it
# can still bind :80 unprivileged; chown the dirs Caddy reads/writes.
RUN addgroup -S web && adduser -S -G web web \
    && chown -R web:web /srv /data /config
USER web
CMD ["caddy", "file-server", "--root", "/srv", "--listen", ":80"]
