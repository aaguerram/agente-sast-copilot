using System.Text.Json;
using RickMorty.Application.Interfaces;
using RickMorty.Domain.Entities;

namespace RickMorty.Infrastructure.Data;

/// <summary>
/// Implementación del puerto con data quemada: en vez de llamar a la API GraphQL de
/// Rick and Morty, lee las respuestas GraphQL capturadas en <c>Data/*.json</c>
/// (recursos embebidos, generados por <c>scripts/capturar-datos.sh</c>).
/// La paginación y el filtro por nombre se resuelven en memoria.
/// </summary>
public class RickMortyJsonDataSource : IRickMortyDataSource
{
    /// <summary>Tamaño de página de la API de origen.</summary>
    private const int PageSize = 20;

    private readonly IReadOnlyList<Character> _characters;
    private readonly IReadOnlyList<Episode> _episodes;
    private readonly IReadOnlyList<Location> _locations;
    private readonly Dictionary<int, Character> _charactersById;
    private readonly Dictionary<int, int[]> _episodeCharacterIds = new();
    private readonly Dictionary<int, int[]> _locationResidentIds = new();

    public RickMortyJsonDataSource()
    {
        _characters = Load("characters.json", "charactersByIds").Select(MapCharacter).ToList();
        _charactersById = _characters.ToDictionary(c => c.Id);

        var episodes = new List<Episode>();
        foreach (var e in Load("episodes.json", "episodesByIds"))
        {
            var episode = MapEpisode(e);
            episodes.Add(episode);
            _episodeCharacterIds[episode.Id] = Ids(e, "characters");
        }
        _episodes = episodes;

        var locations = new List<Location>();
        foreach (var l in Load("locations.json", "locationsByIds"))
        {
            var location = MapLocation(l);
            locations.Add(location);
            _locationResidentIds[location.Id] = Ids(l, "residents");
        }
        _locations = locations;
    }

    public Task<PagedResult<Character>> GetCharactersAsync(
        int page, string? name, CancellationToken ct = default)
        => Task.FromResult(Paginate(FilterByName(_characters, name, c => c.Name), page));

    public Task<Character?> GetCharacterByIdAsync(int id, CancellationToken ct = default)
        => Task.FromResult(_charactersById.GetValueOrDefault(id));

    public Task<PagedResult<Episode>> GetEpisodesAsync(int page, CancellationToken ct = default)
        => Task.FromResult(Paginate(_episodes, page));

    public Task<Episode?> GetEpisodeByIdAsync(int id, CancellationToken ct = default)
        => Task.FromResult(_episodes.FirstOrDefault(e => e.Id == id));

    public Task<IReadOnlyList<Character>?> GetEpisodeCharactersAsync(
        int episodeId, CancellationToken ct = default)
        => Task.FromResult(Characters(_episodeCharacterIds, episodeId));

    public Task<PagedResult<Location>> GetLocationsAsync(
        int page, string? name, CancellationToken ct = default)
        => Task.FromResult(Paginate(FilterByName(_locations, name, l => l.Name), page));

    public Task<Location?> GetLocationByIdAsync(int id, CancellationToken ct = default)
        => Task.FromResult(_locations.FirstOrDefault(l => l.Id == id));

    public Task<IReadOnlyList<Character>?> GetLocationResidentsAsync(
        int locationId, CancellationToken ct = default)
        => Task.FromResult(Characters(_locationResidentIds, locationId));

    // --- helpers ---

    /// <summary>Lee un JSON embebido y devuelve los elementos de <c>data.{field}</c>.</summary>
    private static List<JsonElement> Load(string file, string field)
    {
        var assembly = typeof(RickMortyJsonDataSource).Assembly;
        var resource = $"{typeof(RickMortyJsonDataSource).Namespace}.{file}";
        using var stream = assembly.GetManifestResourceStream(resource)
            ?? throw new InvalidOperationException($"No se encontró el recurso embebido '{resource}'.");
        using var doc = JsonDocument.Parse(stream);
        return doc.RootElement.GetProperty("data").GetProperty(field)
            .EnumerateArray()
            .Where(e => e.ValueKind == JsonValueKind.Object)
            .Select(e => e.Clone())
            .ToList();
    }

    private static IReadOnlyList<T> FilterByName<T>(
        IReadOnlyList<T> items, string? name, Func<T, string> getName)
        => string.IsNullOrWhiteSpace(name)
            ? items
            : items.Where(i => getName(i).Contains(name.Trim(), StringComparison.OrdinalIgnoreCase)).ToList();

    private static PagedResult<T> Paginate<T>(IReadOnlyList<T> items, int page)
    {
        if (page < 1) page = 1;
        var pages = (items.Count + PageSize - 1) / PageSize;
        var skip = (int)Math.Min((long)(page - 1) * PageSize, items.Count);
        return new PagedResult<T>
        {
            Count = items.Count,
            Pages = pages,
            Next = page < pages ? page + 1 : null,
            Prev = page > 1 && pages > 0 ? Math.Min(page - 1, pages) : null,
            Items = items.Skip(skip).Take(PageSize).ToList(),
        };
    }

    /// <summary>Personajes relacionados con un id; <c>null</c> si ese id no existe.</summary>
    private IReadOnlyList<Character>? Characters(Dictionary<int, int[]> relation, int id)
        => relation.TryGetValue(id, out var ids)
            ? ids.Where(_charactersById.ContainsKey).Select(i => _charactersById[i]).ToList()
            : null;

    private static string Str(JsonElement e, string prop) =>
        e.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.String
            ? v.GetString() ?? string.Empty : string.Empty;

    private static int Id(JsonElement e) => int.TryParse(Str(e, "id"), out var id) ? id : 0;

    private static int[] Ids(JsonElement e, string prop) =>
        e.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.Array
            ? v.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.Object).Select(Id).ToArray()
            : Array.Empty<int>();

    private static string NestedName(JsonElement e, string prop) =>
        e.TryGetProperty(prop, out var v) && v.ValueKind == JsonValueKind.Object
            ? Str(v, "name") : string.Empty;

    private static Character MapCharacter(JsonElement e) => new()
    {
        Id = Id(e),
        Name = Str(e, "name"),
        Status = Str(e, "status"),
        Species = Str(e, "species"),
        Type = Str(e, "type"),
        Gender = Str(e, "gender"),
        Image = Str(e, "image"),
        OriginName = NestedName(e, "origin"),
        LocationName = NestedName(e, "location"),
        EpisodeCount = Ids(e, "episode").Length,
    };

    private static Episode MapEpisode(JsonElement e) => new()
    {
        Id = Id(e),
        Name = Str(e, "name"),
        AirDate = Str(e, "air_date"),
        Code = Str(e, "episode"),
    };

    private static Location MapLocation(JsonElement e) => new()
    {
        Id = Id(e),
        Name = Str(e, "name"),
        Type = Str(e, "type"),
        Dimension = Str(e, "dimension"),
        ResidentCount = Ids(e, "residents").Length,
    };
}
