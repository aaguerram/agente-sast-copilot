using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;
using RickMorty.Application.Mapping;

namespace RickMorty.Application.Services;

public class EpisodeService : IEpisodeService
{
    private readonly IRickMortyDataSource _source;

    public EpisodeService(IRickMortyDataSource source) => _source = source;

    public async Task<PagedResultDto<EpisodeDto>> GetEpisodesAsync(int page, CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        var result = await _source.GetEpisodesAsync(page, ct);
        return result.ToDto(e => e.ToDto());
    }

    public async Task<EpisodeDto?> GetByIdAsync(int id, CancellationToken ct = default)
    {
        var episode = await _source.GetEpisodeByIdAsync(id, ct);
        return episode?.ToDto();
    }

    public async Task<IReadOnlyList<CharacterDto>?> GetCharactersAsync(
        int episodeId, CancellationToken ct = default)
    {
        var characters = await _source.GetEpisodeCharactersAsync(episodeId, ct);
        return characters?.Select(c => c.ToDto()).ToList();
    }
}
