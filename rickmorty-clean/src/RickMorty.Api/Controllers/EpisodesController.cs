using System.ComponentModel;
using Microsoft.AspNetCore.Mvc;
using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;

namespace RickMorty.Api.Controllers;

/// <summary>Episodios de Rick and Morty (data quemada en JSON).</summary>
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class EpisodesController : ControllerBase
{
    private readonly IEpisodeService _service;

    public EpisodesController(IEpisodeService service) => _service = service;

    /// <summary>Lista episodios paginados.</summary>
    /// <param name="page">Número de página (desde 1).</param>
    /// <remarks>Ejemplo: <c>GET /api/episodes?page=1</c></remarks>
    /// <response code="200">Página de episodios.</response>
    [HttpGet]
    [ProducesResponseType(typeof(PagedResultDto<EpisodeDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedResultDto<EpisodeDto>>> Get(
        [FromQuery][DefaultValue(1)] int page = 1, CancellationToken ct = default)
        => Ok(await _service.GetEpisodesAsync(page, ct));

    /// <summary>Obtiene un episodio por su id.</summary>
    /// <param name="id">Id del episodio, p. ej. <c>1</c> (Pilot).</param>
    /// <remarks>Ejemplo: <c>GET /api/episodes/1</c></remarks>
    /// <response code="200">El episodio solicitado.</response>
    /// <response code="404">No existe un episodio con ese id.</response>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(EpisodeDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<EpisodeDto>> GetById(
        [DefaultValue(1)] int id = 1, CancellationToken ct = default)
    {
        var episode = await _service.GetByIdAsync(id, ct);
        return episode is null ? NotFound() : Ok(episode);
    }

    /// <summary>Lista los personajes que aparecen en un episodio.</summary>
    /// <param name="id">Id del episodio, p. ej. <c>1</c> (Pilot).</param>
    /// <remarks>Ejemplo: <c>GET /api/episodes/1/characters</c></remarks>
    /// <response code="200">Personajes del episodio.</response>
    /// <response code="404">No existe un episodio con ese id.</response>
    [HttpGet("{id:int}/characters")]
    [ProducesResponseType(typeof(IReadOnlyList<CharacterDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<IReadOnlyList<CharacterDto>>> GetCharacters(
        [DefaultValue(1)] int id = 1, CancellationToken ct = default)
    {
        var characters = await _service.GetCharactersAsync(id, ct);
        return characters is null ? NotFound() : Ok(characters);
    }
}
