# syntax=docker/dockerfile:1.7
# Build con el SDK de .NET 10
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# 1) Solo los manifiestos de proyecto: esta capa se cachea mientras no cambien los .csproj.
#    Si no hay dependencias nuevas, Docker reutiliza el 'restore' y NO descarga nada.
COPY RickMorty.sln .
COPY src/RickMorty.Domain/RickMorty.Domain.csproj           src/RickMorty.Domain/
COPY src/RickMorty.Application/RickMorty.Application.csproj  src/RickMorty.Application/
COPY src/RickMorty.Infrastructure/RickMorty.Infrastructure.csproj src/RickMorty.Infrastructure/
COPY src/RickMorty.Api/RickMorty.Api.csproj                 src/RickMorty.Api/

# 2) Restore con cache mount: los paquetes NuGet persisten entre builds aunque esta capa
#    se re-ejecute (p. ej. al agregar una dependencia), bajando solo lo que falte.
RUN --mount=type=cache,target=/root/.nuget/packages \
    dotnet restore RickMorty.sln

# 3) Ahora el código fuente: cambiar código NO invalida el restore anterior.
COPY src/ src/
RUN --mount=type=cache,target=/root/.nuget/packages \
    dotnet publish src/RickMorty.Api/RickMorty.Api.csproj \
      -c Release -o /app/publish --no-restore

# Runtime ASP.NET 10
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
# Usuario sin privilegios que ya trae la imagen aspnet (APP_UID=1654).
USER $APP_UID
ENTRYPOINT ["dotnet", "RickMorty.Api.dll"]
