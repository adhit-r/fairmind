FROM node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci
COPY . .
# NEXT_PUBLIC_* values are inlined at build time
ARG NEXT_PUBLIC_API_URL=/api/proxy
ARG NEXT_PUBLIC_NEON_REALTIME_URL
ARG NEXT_PUBLIC_AUTHENTIK_URL
ARG NEXT_PUBLIC_AUTHENTIK_CLIENT_ID
ARG NEXT_PUBLIC_AUTHENTIK_REDIRECT_URI
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY
ARG NEXT_PUBLIC_DEMO
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine@sha256:1314fb30ec37592d5845e5a160d522c0e680972aa534549940b8d73bde88481a
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
CMD ["node", "server.js"]
