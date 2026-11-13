# syntax=docker/dockerfile:1.7
# pre-commit con TODOS los hooks de .pre-commit-config.yaml ya instalados (entornos de
# pre-commit-hooks, gitleaks y los hooks locales): correr los hooks no necesita internet ni
# reinstala nada. El contexto es la raíz del repo (ver Dockerfile.dockerignore).
# Si cambias una versión (rev) o dependencia en .pre-commit-config.yaml, reconstruye:
#   docker compose --profile seguridad build pre-commit
FROM python:3.12-slim
ARG PRE_COMMIT_VERSION=4.7.0
ENV PRE_COMMIT_HOME=/opt/pre-commit \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --quiet pre-commit==${PRE_COMMIT_VERSION}
# Los entornos se crean en un repo git vacío con la misma configuración. Se dejan
# escribibles para cualquier UID (el contenedor corre con el usuario del host).
RUN --mount=type=bind,source=.pre-commit-config.yaml,target=/tmp/cfg/.pre-commit-config.yaml \
    git init -q /tmp/repo && cd /tmp/repo \
    && HOME=/tmp/home pre-commit install-hooks -c /tmp/cfg/.pre-commit-config.yaml \
    && rm -rf /tmp/repo /tmp/home /root/.cache \
    && chmod -R a+rwX "$PRE_COMMIT_HOME"
