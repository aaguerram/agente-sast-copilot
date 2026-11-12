// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace BancoFicticio.Controllers;

[Authorize]
[ApiController]
[Route("api/documentos")]
public class DocumentosController : ControllerBase
{
    private readonly DocumentoService _servicio;

    public DocumentosController(DocumentoService servicio) => _servicio = servicio;

    [HttpPost("subir")]
    public async Task<IActionResult> Subir([FromForm] IFormFile archivo)
    {
        using var ms = new MemoryStream();
        await archivo.CopyToAsync(ms);
        var ruta = _servicio.Guardar(archivo.FileName, ms.ToArray());
        return Ok(new { ruta });
    }

    [HttpGet("descargar")]
    public IActionResult Descargar([FromQuery] string nombre)
    {
        return File(_servicio.Leer(nombre), "application/octet-stream");
    }

    [HttpPost("importar")]
    public IActionResult Importar([FromForm] IFormFile archivo)
    {
        var datos = _servicio.Importar(archivo.OpenReadStream());
        return Ok(datos);
    }
}
