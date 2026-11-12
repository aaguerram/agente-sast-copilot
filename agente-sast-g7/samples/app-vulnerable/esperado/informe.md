# Informe — metodología SAST sobre `agente-sast-g7/samples/app-vulnerable`

Ejecución de **referencia**: cada paso se hizo siguiendo su `.agent.md`. Sirve para comparar
lo que produce Copilot sobre la misma muestra.

| Paso | Agente | Hallazgos | Archivo |
|---|---|---|---|
| 1 | ranking-archivos | 8 archivos de riesgo Alto de 15 | `ranking.json` |
| 2 | mapeo-entradas | 15 entradas (11 sin validar) | `entradas.json` |
| 3 | mapeo-operaciones | 15 operaciones peligrosas | `operaciones.json` |
| 4 | trazador-flujos | 11 flujos (1 saneado) | `flujos.json` |
| 5 | analizador-gaps | 10 gaps contra requisitos | `gaps.json` |
| 6 | devils-advocate | 20 sobreviven, 1 refutado | `validacion.json` |
| 7 | priorizador-cwe-owasp | 20 priorizados (16 Alta) | `priorizacion.json` |
| 8 | remediador | 20 recomendaciones | `remediacion.json` |

## Refutado por el devil's advocate

- **F-11** (ORDER BY concatenado): Saneamiento efectivo: ReporteService.cs:42 solo deja pasar fecha, monto o concepto; cualquier otro valor se reemplaza por "fecha" antes del ORDER BY.

## Flujos que cruzan capas

| Id | Flujo | Archivos | Saneamiento |
|---|---|---|---|
| F-01 | Inyección SQL en la búsqueda por titular (CWE-89) | CuentasController.cs → CuentaService.cs → CuentaRepository.cs | parcial |
| F-02 | Inyección SQL con la cookie cliente_id (CWE-89) | CuentasController.cs → CuentaService.cs → CuentaRepository.cs | ninguno |
| F-03 | Inyección SQL en el registro de transferencias (CWE-89) | TransferenciasController.cs → TransferenciaService.cs → TransferenciaRepository.cs | ninguno |
| F-04 | Recorrido de rutas al subir documentos (CWE-22) | DocumentosController.cs → DocumentoService.cs | ninguno |
| F-05 | Recorrido de rutas al descargar documentos (CWE-22) | DocumentosController.cs → DocumentoService.cs | ninguno |
| F-06 | Deserialización con tipos controlados por el cliente (CWE-502) | DocumentosController.cs → DocumentoService.cs | ninguno |
| F-07 | Inyección de comandos al exportar reportes (CWE-78) | ReportesController.cs → ReporteService.cs | ninguno |
| F-08 | Petición del servidor a URL del cliente (SSRF) (CWE-918) | ReportesController.cs → ReporteService.cs | ninguno |
| F-09 | Redirección abierta en login y cierre de sesión (CWE-601) | AuthController.cs | ninguno |
| F-10 | Clave registrada en el log (CWE-532) | AuthController.cs | ninguno |
| F-11 | ORDER BY concatenado en movimientos (CWE-89) | ReportesController.cs → ReporteService.cs → ReporteRepository.cs | completo |

## Matriz final

| Hallazgo | CWE | OWASP | Prioridad | Ubicación | Recomendación |
|---|---|---|---|---|---|
| F-01 Inyección SQL en la búsqueda por titular | CWE-89 | A03:2021-Injection | Alta | `Repositories/CuentaRepository.cs:26` | Consulta parametrizada (SqlParameter); nunca concatenar ni interpolar. |
| F-02 Inyección SQL con la cookie cliente_id | CWE-89 | A03:2021-Injection | Alta | `Repositories/CuentaRepository.cs:38` | Consulta parametrizada (SqlParameter); nunca concatenar ni interpolar. |
| F-03 Inyección SQL en el registro de transferencias | CWE-89 | A03:2021-Injection | Alta | `Repositories/TransferenciaRepository.cs:16` | Consulta parametrizada (SqlParameter); nunca concatenar ni interpolar. |
| F-06 Deserialización con tipos controlados por el cliente | CWE-502 | A08:2021-Software and Data Integrity Failures | Alta | `Services/DocumentoService.cs:29` | TypeNameHandling.None y deserializar a un tipo concreto (o System.Text.Json). |
| F-07 Inyección de comandos al exportar reportes | CWE-78 | A03:2021-Injection | Alta | `Services/ReporteService.cs:27` | No usar shell: ProcessStartInfo con ArgumentList y el formato validado contra {pdf, csv}. |
| G-01 GET /api/cuentas/{id} devuelve cualquier cuenta: la consulta filtra solo por Id, no por el cliente autenticado. | CWE-639 | A01:2021-Broken Access Control | Alta | `Controllers/CuentasController.cs:20` | Tomar el cliente de User (claims) y filtrar cada consulta por ClienteId. |
| G-03 La identidad sale de la cabecera X-Cliente-Id y de la cookie cliente_id (sin firmar), no del token. | CWE-639 | A01:2021-Broken Access Control | Alta | `Controllers/TransferenciasController.cs:19` | Tomar el cliente de User (claims) y filtrar cada consulta por ClienteId. |
| G-06 No se valida monto > 0 ni que la cuenta origen sea del cliente: un monto negativo invierte la transferencia. | CWE-20 | A04:2021-Insecure Design | Alta | `Models/Dtos.cs:6` | Validar con DataAnnotations y rechazar valores fuera del dominio. |
| F-04 Recorrido de rutas al subir documentos | CWE-22 | A01:2021-Broken Access Control | Alta | `Services/DocumentoService.cs:14` | Generar el nombre en el servidor o usar Path.GetFileName y comprobar que la ruta completa empiece por la carpeta base. |
| F-05 Recorrido de rutas al descargar documentos | CWE-22 | A01:2021-Broken Access Control | Alta | `Services/DocumentoService.cs:21` | Generar el nombre en el servidor o usar Path.GetFileName y comprobar que la ruta completa empiece por la carpeta base. |
| F-08 Petición del servidor a URL del cliente (SSRF) | CWE-918 | A10:2021-Server-Side Request Forgery | Alta | `Services/ReporteService.cs:36` | Lista de webhooks permitidos por configuración; rechazar IPs privadas y de metadatos. |
| G-02 CuentasController no tiene [Authorize]: los tres endpoints de cuentas responden sin sesión. | CWE-306 | A07:2021-Identification and Authentication Failures | Alta | `Controllers/CuentasController.cs:10` | [Authorize] en el controlador (o política global con FallbackPolicy). |
| G-04 Transferencias de más de 10 000 se ejecutan sin aprobación: Constantes.UmbralAprobacion no se usa. | CWE-840 | A04:2021-Insecure Design | Alta | `Services/TransferenciaService.cs:24` | Aplicar la regla en el servicio antes de registrar. |
| G-05 No se controla el límite diario de 20 000: Constantes.LimiteDiario no se usa. | CWE-840 | A04:2021-Insecure Design | Alta | `Services/TransferenciaService.cs:24` | Aplicar la regla en el servicio antes de registrar. |
| G-09 La búsqueda por titular devuelve CuentaDto completo, con Saldo y ClienteId de terceros. | CWE-200 | A01:2021-Broken Access Control | Alta | `Controllers/CuentasController.cs:27` | Devolver un DTO de búsqueda sin Saldo ni ClienteId. |
| G-10 El historial de movimientos no comprueba que la cuenta sea del cliente autenticado. | CWE-639 | A01:2021-Broken Access Control | Alta | `Controllers/TransferenciasController.cs:29` | Tomar el cliente de User (claims) y filtrar cada consulta por ClienteId. |
| F-09 Redirección abierta en login y cierre de sesión | CWE-601 | A01:2021-Broken Access Control | Media | `Controllers/AuthController.cs:35` | LocalRedirect o Url.IsLocalUrl. |
| F-10 Clave registrada en el log | CWE-532 | A09:2021-Security Logging and Monitoring Failures | Media | `Controllers/AuthController.cs:19` | No registrar la clave; registrar solo el usuario. |
| G-07 La subida no limita tipo (PDF/imagen) ni tamaño (5 MB) y guarda con el nombre del cliente, no uno generado. | CWE-434 | A04:2021-Insecure Design | Media | `Controllers/DocumentosController.cs:18` | Validar extensión y firma (PDF/imagen), limitar a 5 MB con RequestSizeLimit y guardar con nombre Guid. |
| G-08 El formato de exportación no se limita a pdf o csv. | CWE-20 | A04:2021-Insecure Design | Baja | `Controllers/ReportesController.cs:19` | Validar con DataAnnotations y rechazar valores fuera del dominio. |
