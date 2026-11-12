using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;
using RickMorty.Application.Mapping;

namespace RickMorty.Application.Services;

public class CharacterService : ICharacterService
{
    private readonly IRickMortyDataSource _source;

    public CharacterService(IRickMortyDataSource source) => _source = source;

    public async Task<PagedResultDto<CharacterDto>> GetCharactersAsync(
        int page, string? name, CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        var result = await _source.GetCharactersAsync(page, name, ct);
        return result.ToDto(c => c.ToDto());
    }

    public async Task<CharacterDto?> GetByIdAsync(int id, CancellationToken ct = default)
    {
        var character = await _source.GetCharacterByIdAsync(id, ct);
        return character?.ToDto();
    }
}
