FROM node:22-alpine AS build
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

FROM caddy:2.10-alpine
COPY --from=build /app/dist /srv
# Run as a non-root user. The Caddy binary carries cap_net_bind_service, so it
# can still bind :80 unprivileged; chown the dirs Caddy reads/writes.
RUN addgroup -S web && adduser -S -G web web \
    && chown -R web:web /srv /data /config
USER web
CMD ["caddy", "file-server", "--root", "/srv", "--listen", ":80"]
