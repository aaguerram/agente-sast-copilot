// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using System.Diagnostics;
using BancoFicticio.Models;
using BancoFicticio.Repositories;

namespace BancoFicticio.Services;

public class ReporteService
{
    private static readonly HashSet<string> ColumnasPermitidas = new(StringComparer.OrdinalIgnoreCase)
    {
        "fecha", "monto", "concepto"
    };

    private readonly ReporteRepository _repo;
    private readonly IHttpClientFactory _http;

    public ReporteService(ReporteRepository repo, IHttpClientFactory http)
    {
        _repo = repo;
        _http = http;
    }

    public string Exportar(string formato)
    {
        // El formato llega del cliente y se pega a los argumentos del proceso.
        var proceso = Process.Start("/bin/sh", "-c \"/opt/banco/exportar --formato " + formato + "\"");
        proceso!.WaitForExit();
        return "/var/banco/reportes/ultimo." + formato;
    }

    public async Task Notificar(string webhookUrl, string mensaje)
    {
        // Petición del servidor a cualquier URL que mande el cliente.
        var cliente = _http.CreateClient();
        await cliente.PostAsync(webhookUrl, new StringContent(mensaje));
    }

    public IEnumerable<MovimientoDto> ListarMovimientos(string orden)
    {
        // Saneado: solo columnas de la lista fija; cualquier otro valor usa "fecha".
        var columna = ColumnasPermitidas.Contains(orden) ? orden.ToLowerInvariant() : "fecha";
        return _repo.Movimientos(columna);
    }
}
