# syntax=docker/dockerfile:1.7
# SDK de .NET listo para trabajar SIN internet:
#   - dotnet-sonarscanner ya instalado (lo usa scripts/sonar-analizar.sh);
#   - caché de NuGet (/opt/nuget) con los paquetes de rickmorty-clean, de la app vulnerable
#     de muestra y de los proyectos que haya en objetivos/ AL CONSTRUIR la imagen.
# El contexto es la raíz del repo (ver Dockerfile.dockerignore); el código no queda en la imagen.
# Para incluir los paquetes de un proyecto objetivo nuevo: clónalo en objetivos/ y
#   docker compose --profile seguridad build dotnet-objetivo
FROM mcr.microsoft.com/dotnet/sdk:10.0
ARG SONAR_SCANNER_VERSION=12.1.0
ENV NUGET_PACKAGES=/opt/nuget \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
    PATH="${PATH}:/opt/dotnet-tools"
RUN dotnet tool install dotnet-sonarscanner --version "${SONAR_SCANNER_VERSION}" --tool-path /opt/dotnet-tools
# Restaura cada .csproj en una copia temporal (los de objetivos/ pueden no restaurar: se avisa
# y se sigue). La caché queda escribible para cualquier UID.
RUN --mount=type=bind,target=/ctx \
    mkdir -p /tmp/src "$NUGET_PACKAGES" && cp -r /ctx/. /tmp/src/ \
    && find /tmp/src -name '*.csproj' | sort | while IFS= read -r proj; do \
         echo ">> restore ${proj#/tmp/src/}"; \
         dotnet restore "$proj" -v:quiet || { \
           case "$proj" in /tmp/src/objetivos/*) echo "AVISO: no se pudo restaurar ${proj#/tmp/src/}" ;; *) exit 1 ;; esac; }; \
       done \
    && rm -rf /tmp/src /root/.nuget /root/.local /tmp/NuGetScratch* \
    && chmod -R a+rwX "$NUGET_PACKAGES" /opt/dotnet-tools
