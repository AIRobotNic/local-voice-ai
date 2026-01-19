# syntax=docker/dockerfile:1
# Вышеуказанная строка обязательна для работы кеширования!

FROM node:20-slim AS base
WORKDIR /app

# Настройка PNPM и путей для кеширования
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack prepare pnpm@latest --activate

# --- Этап 1: Установка зависимостей ---
FROM base AS deps
COPY package.json pnpm-lock.yaml ./

# МОНТИРУЕМ КЕШ: Здесь магия. Пакеты не качаются заново, если они уже есть в системе.
RUN --mount=type=cache,target=/pnpm/store \
    pnpm install --frozen-lockfile

# --- Этап 2: Сборка (Build) ---
FROM base AS build
ARG NEXT_PUBLIC_LIVEKIT_URL
# Прокидываем переменную во время сборки для Next.js
ENV NEXT_PUBLIC_LIVEKIT_URL=${NEXT_PUBLIC_LIVEKIT_URL}

# Копируем установленные зависимости из предыдущего этапа
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# МОНТИРУЕМ КЕШ ДЛЯ NEXT.JS: Ускоряет повторную компиляцию (incremental build)
RUN --mount=type=cache,target=/app/.next/cache \
    pnpm run build

# --- Этап 3: Запуск (Runner) ---
FROM base AS runner
ENV NODE_ENV=production

# Переменные для работы приложения
ENV LIVEKIT_URL=http://livekit:7880 \
    LIVEKIT_API_KEY=devkey \
    LIVEKIT_API_SECRET=secret \
    NEXT_PUBLIC_LIVEKIT_URL=${NEXT_PUBLIC_LIVEKIT_URL:-ws://localhost:7880}

# Копируем только то, что нужно для работы, чтобы образ был легким
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 3000

# Запуск через встроенный сервер Next.js
CMD ["node", "node_modules/next/dist/bin/next", "start", "-H", "0.0.0.0", "-p", "3000"]