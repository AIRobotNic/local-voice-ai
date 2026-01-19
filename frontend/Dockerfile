FROM node:20-slim AS base
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate

# --- Слой зависимостей ---
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
# Используем кеш-директорию для pnpm, чтобы не качать пакеты заново
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile

# --- Слой сборки ---
FROM base AS build
ARG NEXT_PUBLIC_LIVEKIT_URL
ENV NEXT_PUBLIC_LIVEKIT_URL=${NEXT_PUBLIC_LIVEKIT_URL:-ws://localhost:7880}

COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Кешируем папку .next/cache для ускорения инкрементальной сборки Next.js
RUN --mount=type=cache,target=/app/.next/cache \
    pnpm run build

# --- Финальный слой (Runner) ---
FROM base AS runner
ENV NODE_ENV=production
# Копируем только необходимые файлы для запуска, чтобы образ был легким
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 3000
CMD ["node", "node_modules/next/dist/bin/next", "start", "-H", "0.0.0.0", 