namespace RickMorty.Application.DTOs;

/// <summary>Página de resultados devuelta por la API REST.</summary>
public record PagedResultDto<T>(
    int Count,
    int Pages,
    int? Next,
    int? Prev,
    IReadOnlyList<T> Items);
