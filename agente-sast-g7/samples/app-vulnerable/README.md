# app-vulnerable — Banco Ficticio (muestra para la metodología SAST)

!!! danger "Código vulnerable a propósito"
    API ASP.NET Core (.NET 10) **sintética** con fallas introducidas a propósito para que
    cada paso de la metodología SAST encuentre algo. Datos ficticios. No usar en ningún
    entorno real.

- Capas: `Controllers/` → `Services/` → `Repositories/`, más `Models/`.
- Compila (`dotnet build` en `mcr.microsoft.com/dotnet/sdk:10.0`), pero **no** está en
  `rickmorty-clean/RickMorty.sln`: el pipeline no la compila ni la analiza SonarQube.
- Excluida de los controles bloqueantes igual que todo `agente-sast-g7/samples/`
  (`.semgrepignore`, `.gitleaks.toml`, `exclude` de los hooks .NET en `.pre-commit-config.yaml`).
- `REQUISITOS.md`: historias de usuario, reglas de negocio y modelo de amenazas que el
  código incumple (entrada del paso `analizador-gaps`).
- `esperado/`: **respuesta de referencia** de cada paso (JSON + `informe.md`) y
  `fallas-esperadas.json`, que usan las pruebas de `agente-sast-g7/scripts/metodologia.py`.

## Inventario de fallas

### Flujos fuente → sumidero (paso 4)

| Id | Falla | CWE | Camino |
|---|---|---|---|
| F-01 | SQL concatenado en búsqueda por titular | 89 | `CuentasController.Buscar` → `CuentaService.BuscarPorTitular` (solo `Trim`) → `CuentaRepository.BuscarPorTitular` |
| F-02 | SQL interpolado con la cookie `cliente_id` | 89 | `CuentasController.Mias` → `CuentaService.DeCliente` → `CuentaRepository.DeCliente` |
| F-03 | SQL concatenado al registrar transferencias | 89 | `TransferenciasController.Crear` → `TransferenciaService.Ejecutar` → `TransferenciaRepository.Registrar` |
| F-04 | Recorrido de rutas al subir (`FileName`) | 22 | `DocumentosController.Subir` → `DocumentoService.Guardar` |
| F-05 | Recorrido de rutas al descargar | 22 | `DocumentosController.Descargar` → `DocumentoService.Leer` |
| F-06 | Deserialización con `TypeNameHandling.All` | 502 | `DocumentosController.Importar` → `DocumentoService.Importar` |
| F-07 | Inyección de comandos (`/bin/sh -c`) | 78 | `ReportesController.Exportar` → `ReporteService.Exportar` |
| F-08 | SSRF con `WebhookUrl` | 918 | `ReportesController.Notificar` → `ReporteService.Notificar` |
| F-09 | Redirección abierta | 601 | `AuthController.Login` / `Salir` |
| F-10 | Clave en el log | 532 | `AuthController.Login` |
| **F-11** | **Falso positivo:** `ORDER BY` concatenado, pero con lista blanca | — | `ReportesController.Movimientos` → `ReporteService.ListarMovimientos` → `ReporteRepository.Movimientos` |

F-11 está para que `devils-advocate` tenga algo que **refutar**.

### Gaps contra requisitos (paso 5)

| Id | Requisito | Falla | CWE |
|---|---|---|---|
| G-01 | RN-01 | IDOR: `GET /api/cuentas/{id}` no filtra por cliente | 639 |
| G-02 | RN-05 | `CuentasController` sin `[Authorize]` | 306 |
| G-03 | RN-04 | Identidad desde cabecera `X-Cliente-Id` y cookie sin firmar | 639 |
| G-04 | RN-02 | Transferencias > 10 000 sin aprobación (`UmbralAprobacion` sin uso) | 840 |
| G-05 | RN-03 | Sin límite diario (`LimiteDiario` sin uso) | 840 |
| G-06 | HU-03 | Monto negativo y cuenta origen sin verificar | 20 |
| G-07 | HU-04 | Subida sin tipo, tamaño ni nombre generado | 434 |
| G-08 | HU-05 | Formato de exportación libre | 20 |
| G-09 | HU-02 | La búsqueda expone saldos y `ClienteId` de terceros | 200 |
| G-10 | RN-01 | Historial de movimientos sin verificar propietario | 639 |

### Para los pasos 1–3

- **Ranking:** alto riesgo en controladores de cuentas, autenticación y documentos y en
  `ReporteService`/`DocumentoService`; bajo en `Dtos.cs` y `Constantes.cs`.
- **Entradas:** query, ruta, cuerpo, cabecera (`X-Cliente-Id`), cookie (`cliente_id`),
  formulario y archivo (`IFormFile`, `FileName`).
- **Operaciones:** SQL dinámico, `Process.Start`, `Path.Combine`/`File.*`,
  `TypeNameHandling.All`, `PostAsync(url)`, `Redirect(url)`, log con la clave.
