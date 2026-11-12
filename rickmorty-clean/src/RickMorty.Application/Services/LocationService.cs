using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;
using RickMorty.Application.Mapping;

namespace RickMorty.Application.Services;

public class LocationService : ILocationService
{
    private readonly IRickMortyDataSource _source;

    public LocationService(IRickMortyDataSource source) => _source = source;

    public async Task<PagedResultDto<LocationDto>> GetLocationsAsync(
        int page, string? name, CancellationToken ct = default)
    {
        if (page < 1) page = 1;
        var result = await _source.GetLocationsAsync(page, name, ct);
        return result.ToDto(l => l.ToDto());
    }

    public async Task<LocationDto?> GetByIdAsync(int id, CancellationToken ct = default)
    {
        var location = await _source.GetLocationByIdAsync(id, ct);
        return location?.ToDto();
    }

    public async Task<IReadOnlyList<CharacterDto>?> GetResidentsAsync(
        int locationId, CancellationToken ct = default)
    {
        var residents = await _source.GetLocationResidentsAsync(locationId, ct);
        return residents?.Select(c => c.ToDto()).ToList();
    }
}
