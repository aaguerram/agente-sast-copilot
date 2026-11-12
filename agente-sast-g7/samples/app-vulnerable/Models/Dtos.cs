// Muestra DELIBERADAMENTE vulnerable (datos sintéticos). Archivo de bajo riesgo: solo DTOs.
namespace BancoFicticio.Models;

public record CuentaDto(int Id, int ClienteId, string Titular, string Numero, decimal Saldo);

public record TransferenciaDto(int CuentaOrigenId, string CuentaDestino, decimal Monto, string Concepto);

public record LoginDto(string Usuario, string Clave, string? ReturnUrl);

public record NotificacionDto(string WebhookUrl, string Mensaje);

public record MovimientoDto(DateTime Fecha, string Concepto, decimal Monto);
