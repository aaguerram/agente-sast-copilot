// Muestra DELIBERADAMENTE vulnerable (datos sintéticos). Archivo de bajo riesgo: constantes.
namespace BancoFicticio.Models;

public static class Constantes
{
    // Reglas de negocio de REQUISITOS.md. Están definidas, pero el código no las usa.
    public const decimal UmbralAprobacion = 10_000m;
    public const decimal LimiteDiario = 20_000m;

    public const string MonedaPorDefecto = "USD";
    public const int TamanoPagina = 50;
}
