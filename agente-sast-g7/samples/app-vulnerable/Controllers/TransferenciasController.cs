// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using BancoFicticio.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace BancoFicticio.Controllers;

[Authorize]
[ApiController]
[Route("api/transferencias")]
public class TransferenciasController : ControllerBase
{
    private readonly TransferenciaService _servicio;

    public TransferenciasController(TransferenciaService servicio) => _servicio = servicio;

    [HttpPost]
    public IActionResult Crear([FromBody] TransferenciaDto dto, [FromHeader(Name = "X-Cliente-Id")] string clienteId)
    {
        // El cliente se toma de una cabecera en vez del token.
        var id = _servicio.Ejecutar(dto, clienteId);
        return Ok(new { id });
    }

    [HttpGet("historial")]
    public IActionResult Historial([FromQuery] int cuentaId)
    {
        return Ok(_servicio.Historial(cuentaId));
    }
}
