using System.ComponentModel;
using Microsoft.AspNetCore.Mvc;
using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;

namespace RickMorty.Api.Controllers;

/// <summary>Personajes de Rick and Morty (data quemada en JSON).</summary>
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class CharactersController : ControllerBase
{
    private readonly ICharacterService _service;

    public CharactersController(ICharacterService service) => _service = service;

    /// <summary>Lista personajes paginados, con filtro opcional por nombre.</summary>
    /// <param name="page">Número de página (desde 1).</param>
    /// <param name="name">Filtro por nombre, p. ej. <c>rick</c>.</param>
    /// <remarks>
    /// Ejemplo: <c>GET /api/characters?page=1&amp;name=rick</c>
    /// </remarks>
    /// <response code="200">Página de personajes.</response>
    [HttpGet]
    [ProducesResponseType(typeof(PagedResultDto<CharacterDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedResultDto<CharacterDto>>> Get(
        [FromQuery][DefaultValue(1)] int page = 1,
        [FromQuery][DefaultValue("rick")] string? name = "rick",
        CancellationToken ct = default)
        => Ok(await _service.GetCharactersAsync(page, name, ct));

    /// <summary>Obtiene un personaje por su id.</summary>
    /// <param name="id">Id del personaje, p. ej. <c>1</c> (Rick Sanchez).</param>
    /// <remarks>Ejemplo: <c>GET /api/characters/1</c></remarks>
    /// <response code="200">El personaje solicitado.</response>
    /// <response code="404">No existe un personaje con ese id.</response>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(CharacterDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<CharacterDto>> GetById(
        [DefaultValue(1)] int id = 1, CancellationToken ct = default)
    {
        var character = await _service.GetByIdAsync(id, ct);
        return character is null ? NotFound() : Ok(character);
    }
}
