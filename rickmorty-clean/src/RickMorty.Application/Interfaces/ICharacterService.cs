using RickMorty.Application.DTOs;

namespace RickMorty.Application.Interfaces;

public interface ICharacterService
{
    Task<PagedResultDto<CharacterDto>> GetCharactersAsync(int page, string? name, CancellationToken ct = default);
    Task<CharacterDto?> GetByIdAsync(int id, CancellationToken ct = default);
}
