namespace RickMorty.Application.DTOs;

/// <summary>Personaje expuesto por la API REST.</summary>
public record CharacterDto(
    int Id,
    string Name,
    string Status,
    string Species,
    string Type,
    string Gender,
    string Image,
    string Origin,
    string Location,
    int EpisodeCount);
