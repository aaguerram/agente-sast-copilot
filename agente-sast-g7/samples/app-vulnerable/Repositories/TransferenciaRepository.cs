// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using Microsoft.Data.SqlClient;

namespace BancoFicticio.Repositories;

public class TransferenciaRepository
{
    private readonly string _cadena;

    public TransferenciaRepository(IConfiguration config) => _cadena = config.GetConnectionString("Banco")!;

    public int Registrar(int origen, string destino, decimal monto, string concepto)
    {
        using var conn = new SqlConnection(_cadena);
        var sql = "INSERT INTO Transferencias (Origen, Destino, Monto, Concepto) OUTPUT INSERTED.Id VALUES ("
                  + origen + ", '" + destino + "', " + monto + ", '" + concepto + "')";
        using var cmd = new SqlCommand(sql, conn);
        conn.Open();
        return (int)cmd.ExecuteScalar();
    }

    public IEnumerable<MovimientoDto> Historial(int cuentaId)
    {
        using var conn = new SqlConnection(_cadena);
        using var cmd = new SqlCommand("SELECT Fecha, Concepto, Monto FROM Movimientos WHERE CuentaId = @c", conn);
        cmd.Parameters.AddWithValue("@c", cuentaId);
        conn.Open();
        using var r = cmd.ExecuteReader();
        var lista = new List<MovimientoDto>();
        while (r.Read()) lista.Add(new MovimientoDto(r.GetDateTime(0), r.GetString(1), r.GetDecimal(2)));
        return lista;
    }
}
