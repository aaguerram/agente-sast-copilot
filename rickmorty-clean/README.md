# rickmorty-clean — API REST sobre Rick and Morty (data quemada)

API REST en **.NET 10** con **arquitectura limpia** sobre los datos de Rick and Morty,
documentada en **Swagger** con ejemplos de consumo. Trabaja con **data quemada**: las
respuestas de la API GraphQL (`https://rickandmortyapi.com/graphql`) están capturadas en JSON
dentro de Infrastructure, así que **no hace llamadas externas en tiempo de ejecución**.
Todo corre en **Docker Compose**; no requiere instalar .NET en la máquina.

## Estructura

```
RickMorty.sln
src/
  RickMorty.Domain/          Entidades (Character, Episode, Location, PagedResult). Sin dependencias.
  RickMorty.Application/     Puertos, DTOs, servicios y mapeo. Depende de Domain.
  RickMorty.Infrastructure/  Fuente de datos JSON. Depende de Application.
    Data/characters.json     826 personajes   (respuesta GraphQL de charactersByIds)
    Data/episodes.json       51 episodios     (respuesta GraphQL de episodesByIds)
    Data/locations.json      126 ubicaciones  (respuesta GraphQL de locationsByIds)
    Data/RickMortyJsonDataSource.cs
  RickMorty.Api/             Controllers REST + Swagger. Depende de Application + Infrastructure.
scripts/capturar-datos.sh    Vuelve a capturar la data desde GraphQL
Dockerfile                   Build (sdk:10.0) + runtime (aspnet:10.0)
docker-compose.yml
```

Dependencias (regla de arquitectura limpia): `Api → Application/Infrastructure →
Application → Domain`. El dominio no conoce a nadie; Infrastructure implementa el puerto
`IRickMortyDataSource` que define Application.

## Ejecutar

```bash
docker compose up --build        # http://localhost:8080
```

Swagger queda en la **raíz**: <http://localhost:8080/>. Cambia el puerto con `API_PORT`
(p. ej. `API_PORT=9000 docker compose up --build`).

## Endpoints y ejemplos de consumo

| Método | Ruta | Ejemplo |
|---|---|---|
| GET | `/api/characters` | `GET /api/characters?page=1&name=rick` |
| GET | `/api/characters/{id}` | `GET /api/characters/1` (Rick Sanchez) |
| GET | `/api/episodes` | `GET /api/episodes?page=1` |
| GET | `/api/episodes/{id}` | `GET /api/episodes/1` (Pilot) |
| GET | `/api/episodes/{id}/characters` | `GET /api/episodes/1/characters` |
| GET | `/api/locations` | `GET /api/locations?page=1&name=earth` |
| GET | `/api/locations/{id}` | `GET /api/locations/1` (Earth C-137) |
| GET | `/api/locations/{id}/residents` | `GET /api/locations/1/residents` |

Los listados paginan de 20 en 20 y el filtro `name` busca por coincidencia parcial sin
distinguir mayúsculas. Un id inexistente responde `404`.

```bash
curl "http://localhost:8080/api/characters?page=1&name=rick"
curl "http://localhost:8080/api/characters/1"
curl "http://localhost:8080/api/episodes?page=1"
curl "http://localhost:8080/api/episodes/1"
curl "http://localhost:8080/api/episodes/1/characters"
curl "http://localhost:8080/api/locations?page=1&name=earth"
curl "http://localhost:8080/api/locations/1"
curl "http://localhost:8080/api/locations/1/residents"
```

Respuesta de ejemplo (`/api/characters/1`):

```json
{
  "id": 1,
  "name": "Rick Sanchez",
  "status": "Alive",
  "species": "Human",
  "type": "",
  "gender": "Male",
  "image": "https://rickandmortyapi.com/api/character/avatar/1.jpeg",
  "origin": "Earth (C-137)",
  "location": "Citadel of Ricks",
  "episodeCount": 51
}
```

## Data quemada

`RickMortyJsonDataSource` (en Infrastructure) carga una sola vez los tres JSON, que van
embebidos en el ensamblado, y resuelve en memoria la paginación, el filtro por nombre y las
relaciones (personajes de un episodio, residentes de una ubicación). Cada archivo es la
respuesta GraphQL tal cual, con la forma `{ "data": { "charactersByIds": [ ... ] } }`.

Para refrescar la data desde la API GraphQL (requiere `curl` y `python3`) y reconstruir:

```bash
./scripts/capturar-datos.sh
docker compose up --build
```
