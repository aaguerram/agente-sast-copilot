namespace RickMorty.Application.DTOs;

/// <summary>Ubicación expuesta por la API REST.</summary>
public record LocationDto(
    int Id,
    string Name,
    string Type,
    string Dimension,
    int ResidentCount);
