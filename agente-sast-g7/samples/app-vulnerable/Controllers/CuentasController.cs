// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Services;
using Microsoft.AspNetCore.Mvc;

namespace BancoFicticio.Controllers;

// Sin [Authorize]: cualquiera puede consultar cuentas.
[ApiController]
[Route("api/cuentas")]
public class CuentasController : ControllerBase
{
    private readonly CuentaService _servicio;

    public CuentasController(CuentaService servicio) => _servicio = servicio;

    [HttpGet("{id}")]
    public IActionResult Obtener([FromRoute] int id)
    {
        // Devuelve la cuenta sin comprobar que pertenezca al cliente autenticado.
        var cuenta = _servicio.Obtener(id);
        return cuenta is null ? NotFound() : Ok(cuenta);
    }

    [HttpGet("buscar")]
    public IActionResult Buscar([FromQuery] string titular)
    {
        return Ok(_servicio.BuscarPorTitular(titular));
    }

    [HttpGet("mias")]
    public IActionResult Mias()
    {
        // La identidad sale de una cookie que el cliente puede cambiar.
        var clienteId = Request.Cookies["cliente_id"];
        return Ok(_servicio.DeCliente(clienteId!));
    }
}
