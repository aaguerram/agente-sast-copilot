// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using BancoFicticio.Repositories;

namespace BancoFicticio.Services;

public class CuentaService
{
    private readonly CuentaRepository _repo;

    public CuentaService(CuentaRepository repo) => _repo = repo;

    public CuentaDto? Obtener(int id) => _repo.PorId(id);

    public IEnumerable<CuentaDto> BuscarPorTitular(string titular)
    {
        // Solo recorta espacios: no valida ni escapa.
        var filtro = titular.Trim();
        return _repo.BuscarPorTitular(filtro);
    }

    public IEnumerable<CuentaDto> DeCliente(string clienteId) => _repo.DeCliente(clienteId);
}
