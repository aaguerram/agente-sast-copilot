// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using Microsoft.Data.SqlClient;

namespace BancoFicticio.Repositories;

public class ReporteRepository
{
    private readonly string _cadena;

    public ReporteRepository(IConfiguration config) => _cadena = config.GetConnectionString("Banco")!;

    public IEnumerable<MovimientoDto> Movimientos(string columna)
    {
        using var conn = new SqlConnection(_cadena);
        // ORDER BY no admite parámetros: la columna llega ya validada por ReporteService.
        var sql = "SELECT Fecha, Concepto, Monto FROM Movimientos ORDER BY " + columna;
        using var cmd = new SqlCommand(sql, conn);
        conn.Open();
        using var r = cmd.ExecuteReader();
        var lista = new List<MovimientoDto>();
        while (r.Read()) lista.Add(new MovimientoDto(r.GetDateTime(0), r.GetString(1), r.GetDecimal(2)));
        return lista;
    }
}
