# Azure CLI + git, para correr scripts/ado-bootstrap.sh sin instalar nada en el host.
ARG AZURE_CLI_VERSION=2.91.0
FROM mcr.microsoft.com/azure-cli:${AZURE_CLI_VERSION}
RUN tdnf install -y git && tdnf clean all
