using RickMorty.Application.DTOs;

namespace RickMorty.Application.Interfaces;

public interface ILocationService
{
    Task<PagedResultDto<LocationDto>> GetLocationsAsync(int page, string? name, CancellationToken ct = default);
    Task<LocationDto?> GetByIdAsync(int id, CancellationToken ct = default);
    Task<IReadOnlyList<CharacterDto>?> GetResidentsAsync(int locationId, CancellationToken ct = default);
}
