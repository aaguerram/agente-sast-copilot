// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using Microsoft.AspNetCore.Mvc;

namespace BancoFicticio.Controllers;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly ILogger<AuthController> _logger;

    public AuthController(ILogger<AuthController> logger) => _logger = logger;

    [HttpPost("login")]
    public IActionResult Login([FromBody] LoginDto dto)
    {
        // Registra la clave en texto plano en el log.
        _logger.LogInformation("Intento de login usuario={Usuario} clave={Clave}", dto.Usuario, dto.Clave);

        if (dto.Usuario == "demo" && dto.Clave.Length > 0)
        {
            Response.Cookies.Append("cliente_id", "1001");
            // Redirige a una URL que manda el cliente, sin validar que sea local.
            return Redirect(dto.ReturnUrl ?? "/");
        }

        return Unauthorized();
    }

    [HttpGet("salir")]
    public IActionResult Salir([FromQuery] string volverA)
    {
        Response.Cookies.Delete("cliente_id");
        return Redirect(volverA);
    }
}
