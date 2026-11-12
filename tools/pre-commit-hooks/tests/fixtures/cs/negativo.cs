// Fixture de pruebas: código correcto. NINGUNA regla debe disparar aquí.
// Comentario con URL: https://learn.microsoft.com/dotnet y IP 10.0.0.1 -> se ignora.
/* Bloque con Password=NoCuenta; y new Random() para tokens -> se ignora */
using System;
using System.Security.Cryptography;
using Microsoft.Extensions.Options;

public class Negativo
{
    private const string Xsd = "http://www.w3.org/2001/XMLSchema";
    private const string Soap = "http://schemas.xmlsoap.org/soap/envelope/";
    private const string Relativa = "/api/characters";
    private const string Version = "1.2.3";
    private const string ClaveConfig = "Jwt:SigningKey";
    private const string VariableEntorno = "API_TOKEN";
    private const string MensajePassword = "La contraseña es obligatoria";
    private const string TokenEndpoint = "https://{0}/oauth/token";
    private string password = "";
    private const string Plantilla = "Server={0};Password={1};";
    public int TokenLifetimeMinutes = 30;
    private readonly string urlDinamica;

    public Negativo(IOptions<Opciones> o)
    {
        urlDinamica = $"https://{o.Value.Host}/v1";
        var ok = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator2;
    }

    public void Tls(HttpClientHandler h)
    {
        h.SslProtocols = System.Security.Authentication.SslProtocols.Tls12 | System.Security.Authentication.SslProtocols.Tls13;
        h.ServerCertificateCustomValidationCallback = (m, c, ch, e) => e == System.Net.Security.SslPolicyErrors.None;
    }

    public byte[] Hash(byte[] d) => SHA256.HashData(d);
    // pre-commit:allow dotnet-hash-debil checksum de compatibilidad con un sistema legado, no es seguridad
    public byte[] Etag(byte[] d) => MD5.HashData(d);
    public string Token() => Convert.ToHexString(RandomNumberGenerator.GetBytes(32));
    public int Dado() => new Random().Next(1, 7);

#pragma warning disable CA1822 // métodos de instancia por contrato de la interfaz pública
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1031", Justification = "Se registra y se relanza arriba")]
    public async System.Threading.Tasks.Task Bien()
    {
        try { await HacerAsync(); }
        catch (OperationCanceledException) { /* cancelación esperada: no es un error */ }
        var r = await ObtenerAsync();
        var resultado = actionResult.Result;
        var conexion = "Server=db;Database=app;Integrated Security=true;";
        var url = "https://api.externa.com"; // pre-commit:allow dotnet-url-quemada dominio fijo por contrato, documentado en ADR-7
    }
}
