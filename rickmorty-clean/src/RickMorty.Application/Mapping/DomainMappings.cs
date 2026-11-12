using RickMorty.Application.DTOs;
using RickMorty.Domain.Entities;

namespace RickMorty.Application.Mapping;

/// <summary>Mapea entidades de dominio a DTOs de la API REST.</summary>
public static class DomainMappings
{
    public static CharacterDto ToDto(this Character c) => new(
        c.Id, c.Name, c.Status, c.Species, c.Type, c.Gender, c.Image,
        c.OriginName, c.LocationName, c.EpisodeCount);

    public static EpisodeDto ToDto(this Episode e) => new(e.Id, e.Name, e.AirDate, e.Code);

    public static LocationDto ToDto(this Location l) => new(
        l.Id, l.Name, l.Type, l.Dimension, l.ResidentCount);

    public static PagedResultDto<TDto> ToDto<TSrc, TDto>(
        this PagedResult<TSrc> page, Func<TSrc, TDto> map) => new(
        page.Count, page.Pages, page.Next, page.Prev,
        page.Items.Select(map).ToList());
}
