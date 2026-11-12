// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using Microsoft.Data.SqlClient;

namespace BancoFicticio.Repositories;

public class CuentaRepository
{
    private readonly string _cadena;

    public CuentaRepository(IConfiguration config) => _cadena = config.GetConnectionString("Banco")!;

    public CuentaDto? PorId(int id)
    {
        using var conn = new SqlConnection(_cadena);
        using var cmd = new SqlCommand("SELECT Id, ClienteId, Titular, Numero, Saldo FROM Cuentas WHERE Id = @id", conn);
        cmd.Parameters.AddWithValue("@id", id);
        conn.Open();
        using var r = cmd.ExecuteReader();
        return r.Read() ? Mapear(r) : null;
    }

    public IEnumerable<CuentaDto> BuscarPorTitular(string titular)
    {
        using var conn = new SqlConnection(_cadena);
        var sql = "SELECT Id, ClienteId, Titular, Numero, Saldo FROM Cuentas WHERE Titular LIKE '%" + titular + "%'";
        using var cmd = new SqlCommand(sql, conn);
        conn.Open();
        using var r = cmd.ExecuteReader();
        var lista = new List<CuentaDto>();
        while (r.Read()) lista.Add(Mapear(r));
        return lista;
    }

    public IEnumerable<CuentaDto> DeCliente(string clienteId)
    {
        using var conn = new SqlConnection(_cadena);
        using var cmd = new SqlCommand($"SELECT Id, ClienteId, Titular, Numero, Saldo FROM Cuentas WHERE ClienteId = {clienteId}", conn);
        conn.Open();
        using var r = cmd.ExecuteReader();
        var lista = new List<CuentaDto>();
        while (r.Read()) lista.Add(Mapear(r));
        return lista;
    }

    private static CuentaDto Mapear(SqlDataReader r) =>
        new(r.GetInt32(0), r.GetInt32(1), r.GetString(2), r.GetString(3), r.GetDecimal(4));
}
