
# Stage 1: Build the Next.js application
FROM oven/bun:1.1.17 as builder

WORKDIR /app

# Install dependencies
COPY apps/frontend/package.json apps/frontend/bun.lock ./apps/frontend/
RUN bun install --frozen-lockfile

# Copy the rest of the frontend application code
COPY apps/frontend/ ./apps/frontend/

# Build the Next.js application
RUN bun run build

# Stage 2: Create a lean production image
FROM oven/bun:1.1.17-alpine

WORKDIR /app

# Set environment variables for Next.js production
ENV NODE_ENV=production

# Copy only necessary files from the builder stage
COPY --from=builder /app/apps/frontend/.next/standalone ./apps/frontend/.next/standalone
COPY --from=builder /app/apps/frontend/.next/static ./apps/frontend/.next/static
COPY --from=builder /app/apps/frontend/public ./apps/frontend/public
COPY --from=builder /app/apps/frontend/node_modules ./apps/frontend/node_modules

# Expose the port Next.js runs on
EXPOSE 3000

# Command to run the application
CMD ["bun", "run", "start"]
