// Código DELIBERADAMENTE vulnerable, solo para demos del agente SAST (datos sintéticos).
// NO usar en producción. Cada método dispara una regla distinta de Semgrep.
using System.Data.SqlClient;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/[controller]")]
public class VulnerableController : ControllerBase
{
    // CWE-89: SQL Injection — concatenación de entrada del usuario en la consulta.
    [HttpGet("usuario")]
    public IActionResult GetUsuario(string nombre)
    {
        var conn = new SqlConnection("Server=.;Database=demo;Trusted_Connection=True;");
        var cmd = new SqlCommand("SELECT * FROM Usuarios WHERE Nombre = '" + nombre + "'", conn);
        conn.Open();
        var reader = cmd.ExecuteReader();
        return Ok(reader);
    }

    // CWE-79: XSS reflejado — devuelve la entrada sin codificar.
    [HttpGet("saludo")]
    public ContentResult Saludo(string texto)
    {
        return new ContentResult { Content = "<h1>Hola " + texto + "</h1>", ContentType = "text/html" };
    }

    // CWE-798: credenciales embebidas en el código.
    private const string ApiKey = "sk_live_1234567890abcdef";

    // CWE-327: uso de algoritmo criptográfico débil (MD5).
    [HttpGet("hash")]
    public string Hash(string valor)
    {
        using var md5 = System.Security.Cryptography.MD5.Create();
        var bytes = md5.ComputeHash(System.Text.Encoding.UTF8.GetBytes(valor + ApiKey));
        return System.Convert.ToHexString(bytes);
    }
}
