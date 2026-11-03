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
CMD ["caddy", "file-server", "--root", "/srv", "--listen", ":80"]
