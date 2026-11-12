// Fixture de pruebas: cada línea marcada con «ESPERA <id>» debe disparar esa regla.
// Contiene patrones inseguros A PROPÓSITO; está excluido de pre-commit, Semgrep y gitleaks.
using System;
using System.Net.Http;
using System.Runtime.Serialization.Formatters.Binary;
using System.Security.Cryptography;

public class Positivo
{
    private const string Api = "https://api.proveedor-externo.com/v1";                 // ESPERA dotnet-url-quemada
    private const string Broker = "amqp://rabbit.interno:5672";                         // ESPERA dotnet-url-quemada
    private const string Servidor = "10.20.30.40";                                      // ESPERA dotnet-url-quemada
    private static readonly Uri Base = new Uri("http://localhost:5000");                // ESPERA dotnet-url-quemada
    private const string Conexion = "Server=db;Database=app;User Id=sa;Password=Sup3rS3creta!;"; // ESPERA dotnet-credencial-quemada
    private const string Cache = "redis://admin:ClaveRedis99@cache:6379";              // ESPERA dotnet-url-quemada dotnet-credencial-quemada
    public string ApiKey { get; } = "ak_live_9f8e7d6c5b4a";                             // ESPERA dotnet-credencial-quemada
    private string clientSecret = @"Zx81-aa9Q.TT";                                      // ESPERA dotnet-credencial-quemada

    public void Tls()
    {
        var h = new HttpClientHandler();
        h.ServerCertificateCustomValidationCallback = (m, c, ch, e) => true;           // ESPERA dotnet-tls-sin-validar
        h.ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator; // ESPERA dotnet-tls-sin-validar
        h.SslProtocols = System.Security.Authentication.SslProtocols.Tls11;            // ESPERA dotnet-tls-sin-validar
        System.Net.ServicePointManager.ServerCertificateValidationCallback +=            // ESPERA dotnet-tls-sin-validar
            delegate { return true; };
    }

    public void Serializacion(object o)
    {
        var bf = new BinaryFormatter();                                                 // ESPERA dotnet-deserializacion-insegura
        var s = new Newtonsoft.Json.JsonSerializerSettings { TypeNameHandling = TypeNameHandling.Auto }; // ESPERA dotnet-deserializacion-insegura
    }

    public byte[] Hash(byte[] d) => MD5.HashData(d);                                    // ESPERA dotnet-hash-debil
    public byte[] Hash2(byte[] d) { using var s = SHA1.Create(); return s.ComputeHash(d); } // ESPERA dotnet-hash-debil

    public string GenerarToken()
    {
        var rnd = new Random();                                                         // ESPERA dotnet-random-inseguro
        return rnd.Next().ToString();
    }

#pragma warning disable CA5394
    [System.Diagnostics.CodeAnalysis.SuppressMessage("Security", "CA5350")]             // ESPERA dotnet-supresion-sin-justificar
    public void Vacio()
    {
        try { Hacer(); }
        catch (Exception) { }                                                           // ESPERA dotnet-catch-vacio
        var x = ObtenerAsync().Result;                                                  // ESPERA dotnet-async-bloqueante
        ObtenerAsync().Wait();                                                          // ESPERA dotnet-async-bloqueante
        var y = ObtenerAsync().GetAwaiter().GetResult();                                // ESPERA dotnet-async-bloqueante
    }
}
