// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using BancoFicticio.Models;
using BancoFicticio.Repositories;

namespace BancoFicticio.Services;

public class TransferenciaService
{
    private readonly TransferenciaRepository _repo;
    private readonly ILogger<TransferenciaService> _logger;

    public TransferenciaService(TransferenciaRepository repo, ILogger<TransferenciaService> logger)
    {
        _repo = repo;
        _logger = logger;
    }

    public int Ejecutar(TransferenciaDto dto, string clienteId)
    {
        // No valida monto positivo, no pide aprobación sobre el umbral
        // ni controla el límite diario (ver REQUISITOS.md).
        _logger.LogInformation("Transferencia cliente={Cliente} destino={Destino} monto={Monto}",
            clienteId, dto.CuentaDestino, dto.Monto);
        return _repo.Registrar(dto.CuentaOrigenId, dto.CuentaDestino, dto.Monto, dto.Concepto);
    }

    public IEnumerable<MovimientoDto> Historial(int cuentaId) => _repo.Historial(cuentaId);
}
