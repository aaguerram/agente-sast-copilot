using System.ComponentModel;
using Microsoft.AspNetCore.Mvc;
using RickMorty.Application.DTOs;
using RickMorty.Application.Interfaces;

namespace RickMorty.Api.Controllers;

/// <summary>Ubicaciones de Rick and Morty (data quemada en JSON).</summary>
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class LocationsController : ControllerBase
{
    private readonly ILocationService _service;

    public LocationsController(ILocationService service) => _service = service;

    /// <summary>Lista ubicaciones paginadas, con filtro opcional por nombre.</summary>
    /// <param name="page">Número de página (desde 1).</param>
    /// <param name="name">Filtro por nombre, p. ej. <c>earth</c>. Vacío = todas.</param>
    /// <remarks>Ejemplo: <c>GET /api/locations?page=1&amp;name=earth</c></remarks>
    /// <response code="200">Página de ubicaciones.</response>
    [HttpGet]
    [ProducesResponseType(typeof(PagedResultDto<LocationDto>), StatusCodes.Status200OK)]
    public async Task<ActionResult<PagedResultDto<LocationDto>>> Get(
        [FromQuery][DefaultValue(1)] int page = 1,
        [FromQuery] string? name = null,
        CancellationToken ct = default)
        => Ok(await _service.GetLocationsAsync(page, name, ct));

    /// <summary>Obtiene una ubicación por su id.</summary>
    /// <param name="id">Id de la ubicación, p. ej. <c>1</c> (Earth C-137).</param>
    /// <remarks>Ejemplo: <c>GET /api/locations/1</c></remarks>
    /// <response code="200">La ubicación solicitada.</response>
    /// <response code="404">No existe una ubicación con ese id.</response>
    [HttpGet("{id:int}")]
    [ProducesResponseType(typeof(LocationDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<LocationDto>> GetById(
        [DefaultValue(1)] int id = 1, CancellationToken ct = default)
    {
        var location = await _service.GetByIdAsync(id, ct);
        return location is null ? NotFound() : Ok(location);
    }

    /// <summary>Lista los personajes que residen en una ubicación.</summary>
    /// <param name="id">Id de la ubicación, p. ej. <c>1</c> (Earth C-137).</param>
    /// <remarks>Ejemplo: <c>GET /api/locations/1/residents</c></remarks>
    /// <response code="200">Residentes de la ubicación.</response>
    /// <response code="404">No existe una ubicación con ese id.</response>
    [HttpGet("{id:int}/residents")]
    [ProducesResponseType(typeof(IReadOnlyList<CharacterDto>), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<IReadOnlyList<CharacterDto>>> GetResidents(
        [DefaultValue(1)] int id = 1, CancellationToken ct = default)
    {
        var residents = await _service.GetResidentsAsync(id, ct);
        return residents is null ? NotFound() : Ok(residents);
    }
}
