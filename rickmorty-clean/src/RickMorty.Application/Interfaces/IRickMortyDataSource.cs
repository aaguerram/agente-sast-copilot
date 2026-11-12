using RickMorty.Domain.Entities;

namespace RickMorty.Application.Interfaces;

/// <summary>
/// Puerto hacia los datos de Rick and Morty. La implementación vive en Infrastructure
/// y lee las respuestas GraphQL capturadas en JSON (data quemada).
/// Los métodos que reciben un id devuelven <c>null</c> cuando ese id no existe.
/// </summary>
public interface IRickMortyDataSource
{
    Task<PagedResult<Character>> GetCharactersAsync(int page, string? name, CancellationToken ct = default);
    Task<Character?> GetCharacterByIdAsync(int id, CancellationToken ct = default);

    Task<PagedResult<Episode>> GetEpisodesAsync(int page, CancellationToken ct = default);
    Task<Episode?> GetEpisodeByIdAsync(int id, CancellationToken ct = default);
    Task<IReadOnlyList<Character>?> GetEpisodeCharactersAsync(int episodeId, CancellationToken ct = default);

    Task<PagedResult<Location>> GetLocationsAsync(int page, string? name, CancellationToken ct = default);
    Task<Location?> GetLocationByIdAsync(int id, CancellationToken ct = default);
    Task<IReadOnlyList<Character>?> GetLocationResidentsAsync(int locationId, CancellationToken ct = default);
}
