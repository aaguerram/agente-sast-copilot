namespace RickMorty.Application.DTOs;

/// <summary>Episodio expuesto por la API REST.</summary>
public record EpisodeDto(
    int Id,
    string Name,
    string AirDate,
    string Code);
