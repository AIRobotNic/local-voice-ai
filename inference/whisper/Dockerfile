# syntax=docker/dockerfile:1
# Вышеуказанная строка обязательна для работы кеширования!

ARG WHISPER_BASE=${WHISPER_BASE:-nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04}

FROM ${WHISPER_BASE}

# 1. Оптимизация переменных окружения
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/data

# 2. Умная установка системных зависимостей с кешированием apt
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Кеширование pip и установка vox-box
# Используем отдельный слой для установки, чтобы не пересобирать его при изменении CMD
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install vox-box

# 4. Проверка устройства (опционально, для отладки в логах)
RUN python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())" || true

# 5. Запуск
# Используем переменную для устройства и модели
ENV VOXBOX_HF_REPO_ID=Systran/faster-whisper-small \
    VOXBOX_DEVICE=cuda

CMD vox-box start \
    --huggingface-repo-id ${VOXBOX_HF_REPO_ID} \
    --data-dir ${DATA_DIR} \
    --device ${VOXBOX_DEVICE}
