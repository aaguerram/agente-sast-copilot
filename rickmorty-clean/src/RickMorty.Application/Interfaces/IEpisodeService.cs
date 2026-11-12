using RickMorty.Application.DTOs;

namespace RickMorty.Application.Interfaces;

public interface IEpisodeService
{
    Task<PagedResultDto<EpisodeDto>> GetEpisodesAsync(int page, CancellationToken ct = default);
    Task<EpisodeDto?> GetByIdAsync(int id, CancellationToken ct = default);
    Task<IReadOnlyList<CharacterDto>?> GetCharactersAsync(int episodeId, CancellationToken ct = default);
}
