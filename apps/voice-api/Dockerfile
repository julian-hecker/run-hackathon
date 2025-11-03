# https://github.com/JuanoD/uv-mono/blob/main/workspace/app/Containerfile

ARG PACKAGE_NAME=voice-api
ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}-slim AS builder

ARG PACKAGE_NAME

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /bin/uv

WORKDIR /app

COPY uv.lock pyproject.toml .python-version /app/

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --package ${PACKAGE_NAME} --no-install-workspace

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-editable --package ${PACKAGE_NAME}


FROM python:${PYTHON_VERSION}-slim AS runner

ARG PACKAGE_NAME

COPY --from=builder /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "-m", "voice_api.main"]