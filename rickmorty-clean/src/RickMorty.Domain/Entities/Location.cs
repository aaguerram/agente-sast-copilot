namespace RickMorty.Domain.Entities;

/// <summary>Ubicación de Rick and Morty (modelo de dominio).</summary>
public class Location
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Dimension { get; set; } = string.Empty;
    public int ResidentCount { get; set; }
}
