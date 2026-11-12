namespace RickMorty.Domain.Entities;

/// <summary>Resultado paginado genérico, reflejando la paginación de la API de origen.</summary>
public class PagedResult<T>
{
    public int Count { get; set; }
    public int Pages { get; set; }
    public int? Next { get; set; }
    public int? Prev { get; set; }
    public IReadOnlyList<T> Items { get; set; } = new List<T>();
}
