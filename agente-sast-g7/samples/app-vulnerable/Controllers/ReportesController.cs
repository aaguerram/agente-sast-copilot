// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using BancoFicticio.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace BancoFicticio.Controllers;

[Authorize]
[ApiController]
[Route("api/reportes")]
public class ReportesController : ControllerBase
{
    private readonly ReporteService _servicio;

    public ReportesController(ReporteService servicio) => _servicio = servicio;

    [HttpGet("exportar")]
    public IActionResult Exportar([FromQuery] string formato)
    {
        return Ok(_servicio.Exportar(formato));
    }

    [HttpPost("notificar")]
    public async Task<IActionResult> Notificar([FromBody] NotificacionDto dto)
    {
        await _servicio.Notificar(dto.WebhookUrl, dto.Mensaje);
        return Accepted();
    }

    // Parece inyectable (ORDER BY concatenado en el repositorio), pero el servicio
    // solo deja pasar columnas de una lista fija.
    [HttpGet("movimientos")]
    public IActionResult Movimientos([FromQuery] string orden)
    {
        return Ok(_servicio.ListarMovimientos(orden));
    }
}
