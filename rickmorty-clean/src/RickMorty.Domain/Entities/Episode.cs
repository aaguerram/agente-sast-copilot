namespace RickMorty.Domain.Entities;

/// <summary>Episodio de Rick and Morty (modelo de dominio).</summary>
public class Episode
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string AirDate { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
}
