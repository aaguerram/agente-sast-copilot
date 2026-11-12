# Criterios de riesgo: CWE, OWASP, criticidad y falsos positivos

Base de conocimiento que usan los agentes de la metodología para que **dos corridas sobre
el mismo código den la misma clasificación**. El modelo no decide de memoria: elige el
CWE con la evidencia del código y lo demás sale de tablas versionadas en el repo.

| Pregunta | Quién la responde | Fuente |
|---|---|---|
| ¿Es un falso positivo? | `devils-advocate` (paso 6) | Checklist de refutación + [criterios de saneamiento](#criterios-de-saneamiento-y-falsos-positivos-conocidos-cnet) de esta página |
| ¿Qué CWE es? | `priorizador-cwe-owasp` (paso 7) elige; la KB lo valida | `agente-sast-g7/kb/cwe-owasp.json` (catálogo oficial MITRE CWE) |
| ¿Qué categoría OWASP? | **La KB**, no el modelo | Vista oficial de MITRE **CWE-1344** (OWASP Top Ten 2021) |
| ¿Qué severidad y prioridad? | `priorizador-cwe-owasp` aplicando la [matriz](#matriz-de-criticidad-owasp-risk-rating-adaptada-a-banca) | OWASP Risk Rating Methodology, adaptada a banca |
| ¿Qué requisitos revisar si el proyecto no trae los suyos? | `analizador-gaps` (paso 5) | `agente-sast-g7/kb/asvs-requisitos.md` (OWASP ASVS 5.0.0, L1/L2) |
| ¿Qué referencia citar en la corrección? | `remediador` (paso 8) | `agente-sast-g7/kb/cheatsheets.json` (OWASP Cheat Sheet Series) |

## Base de conocimiento (`agente-sast-g7/kb/`)

Todo está versionado y funciona **sin red** (red interna del banco). Se regenera con
Docker cuando MITRE u OWASP publican una versión nueva:

```bash
docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_cwe.py    # MITRE CWE
docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb_asvs.py   # OWASP ASVS
docker compose --profile agentes run --rm py agente-sast-g7/scripts/kb.py CWE-89 CWE-639  # consulta
```

| Archivo | Contenido | Licencia |
|---|---|---|
| `cwe-owasp.json` | Cada CWE (debilidades y agrupaciones) con `nombre`, `abstraccion`, `uso` (Mapping Notes de MITRE), `probabilidad` de explotación, `impacto` (C/I/D), `padre`, `owasp_2021` (vista CWE-1344) y `owasp_2025_rc1` (vista CWE-1450, informativa) | Términos de uso de MITRE CWE |
| `asvs-requisitos.md` | 192 controles verificables de OWASP ASVS 5.0.0, niveles L1 y L2, con su ID (`ASVS-V8.2.2`) | CC BY-SA 4.0 (OWASP) |
| `cheatsheets.json` | Índice CWE → hojas de OWASP Cheat Sheet Series (URL oficial) | CC BY-SA 4.0 (OWASP) |

### Cómo se elige el CWE

1. El más **concreto** que describa la causa raíz (nivel `Base` o `Variant`).
2. Con `uso` **`Allowed`** (o `Allowed-with-Review`, justificándolo). MITRE marca como
   `Discouraged` o `Prohibited` las clases genéricas y las agrupaciones (p. ej. `CWE-20`,
   `CWE-200`, `CWE-284`, `CWE-840`): si el primer candidato es uno de ellos, baja a un hijo
   (`CWE-20` → `CWE-1284` cantidad, `CWE-1287` tipo; `CWE-200` → `CWE-359` datos
   personales; `CWE-840` → `CWE-841` flujo de negocio).
3. La categoría OWASP **se copia** de `owasp_2021`. Si el CWE no está en la vista, se usa la
   de su `padre` (`kb.owasp_de` lo hace) y se anota en `notas`; si tampoco, queda vacía.

`metodologia.py validar <RUN>` lo comprueba: CWE inexistente = **error**; CWE desaconsejado
u OWASP distinto del oficial = **aviso**.

## Matriz de criticidad (OWASP Risk Rating adaptada a banca)

La [OWASP Risk Rating Methodology](https://owasp.org/www-community/OWASP_Risk_Rating_Methodology)
estima el riesgo como **probabilidad × impacto**. Para que el agente la aplique igual en
cada corrida, cada factor se reduce a tres niveles con criterios observables en el código.

### Probabilidad (exposición del punto de entrada)

| Nivel | Criterio (el más alto que se cumpla) |
|---|---|
| **Alta** | Endpoint **sin autenticación** (`[AllowAnonymous]` o sin `[Authorize]`) o dato que el cliente controla del todo (query, ruta, cuerpo, cabecera, cookie) y llega al sumidero **sin saneamiento** (`saneamiento: ninguno`). También sube a Alta si la KB marca `probabilidad: High` y el flujo es directo |
| **Media** | Requiere usuario autenticado, o hay saneamiento `parcial`, o el dato atraviesa varias capas con transformaciones que dificultan el abuso |
| **Baja** | Solo alcanzable por un rol administrativo o interno, o requiere condiciones poco probables (configuración no por defecto, carrera) |

### Impacto (qué se pierde si se explota)

| Nivel | Criterio (el más alto que se cumpla) |
|---|---|
| **Alto** | **Dinero** (transferencias, pagos, saldos, límites), **datos de clientes** de terceros (lectura o escritura masiva, IDOR), **ejecución de código o comandos** en el servidor, suplantación de identidad, credenciales o secretos expuestos |
| **Medio** | Datos de un solo cliente o no sensibles, redirección abierta, fuga de información técnica (trazas, rutas), denegación de servicio acotada |
| **Bajo** | Sin efecto directo en confidencialidad, integridad ni disponibilidad: falta de validación de formato, higiene de código, defensa en profundidad |

Pista de la KB: el campo `impacto` del CWE (`C`, `I`, `D`) indica qué dimensiones puede
afectar; el agente decide el nivel con el contexto de negocio.

### Severidad resultante

| Probabilidad ↓ / Impacto → | Bajo | Medio | Alto |
|---|---|---|---|
| **Alta** | Media | Alta | **Crítica** |
| **Media** | Baja | Media | Alta |
| **Baja** | Baja | Baja | Media |

### Prioridad e incidencias

| Severidad | Prioridad | ¿Crea incidencia en Boards? |
|---|---|---|
| Crítica | Alta | Sí (tras aprobación humana) |
| Alta | Alta | Sí (tras aprobación humana) |
| Media | Media | No, queda en el informe |
| Baja | Baja | No, queda en el informe |

- **Hallazgos de herramientas (`/sast`):** la severidad viene del `level` SARIF
  (`error` → Alta, `warning` → Media, `note` → Baja; ver `.github/copilot-instructions.md`)
  y **no se cambia**. La matriz solo se usa para explicar el riesgo en `contexto`.
- **Flujos y gaps (metodología):** no hay severidad de herramienta; se aplica la matriz y
  se escribe en `contexto` la justificación con los dos factores, p. ej.
  `Probabilidad Alta (endpoint sin [Authorize], G-02) × Impacto Alto (datos de clientes) → Crítica`.

## Criterios de saneamiento y falsos positivos conocidos (C#/.NET)

Los usa el `devils-advocate` (paso 6) para refutar con evidencia `archivo:línea`. Un
hallazgo solo se refuta si el control **está en el camino del dato** y **cubre todos los
casos**; si cubre algunos, el saneamiento es `parcial` y el hallazgo **sobrevive** con
probabilidad Media.

| CWE | Saneamiento válido (refuta) | No es saneamiento (sobrevive) |
|---|---|---|
| CWE-89 SQL | `SqlParameter` / `AddWithValue` / `@param`, EF Core LINQ, `FromSqlInterpolated`, Dapper con objeto de parámetros; `ORDER BY`/columna dinámica contra **lista blanca fija** | Concatenación o `string.Format`/interpolación en `SqlCommand`, `FromSqlRaw` con interpolación, escapar comillas a mano, `Replace("'", "")` |
| CWE-78 Comandos | Ejecutable fijo + argumentos de lista blanca o `ProcessStartInfo.ArgumentList` con valores validados; sin `cmd /c` ni `sh -c` | Concatenar en `Arguments`, `UseShellExecute = true` con entrada del cliente, filtrar solo `;` o `&` |
| CWE-22 Rutas | `Path.GetFileName` + `Path.GetFullPath` y comprobar que empieza por la carpeta base; nombre generado por el servidor (GUID) | Solo `Replace("..", "")`, solo `Path.Combine` (acepta rutas absolutas), validar la extensión |
| CWE-79 XSS | Razor con `@` (codifica por defecto), `HtmlEncoder`, respuesta JSON con `Content-Type` correcto | `Html.Raw`, `MarkupString`, construir HTML con cadenas |
| CWE-502 Deserialización | `System.Text.Json` sin polimorfismo, `TypeNameHandling.None`, `SerializationBinder` con lista blanca | `BinaryFormatter`, `TypeNameHandling.Auto/All/Objects` sin binder, `NetDataContractSerializer` |
| CWE-918 SSRF | URL de configuración, o host contra lista blanca tras resolver; `HttpClient` con `BaseAddress` fija y ruta relativa validada | Validar solo el esquema, lista negra de `localhost`, `Uri.IsWellFormedUriString` |
| CWE-601 Redirección | `LocalRedirect`, `Url.IsLocalUrl`, lista blanca de destinos | `Redirect(returnUrl)` sin comprobar, `StartsWith("/")` (acepta `//evil`) |
| CWE-639 / CWE-862 Autorización | `[Authorize]` + filtro por el cliente **del token** (`User.FindFirst(...)`) en la consulta; política con `IAuthorizationHandler` sobre el recurso | Identidad tomada de cabecera, cookie, query o cuerpo; `[Authorize]` sin comprobar la propiedad del recurso |
| CWE-532 Logs | Plantillas estructuradas sin datos sensibles, enmascarado (`****1234`) | Registrar el objeto completo, la clave o el token |

**Falsos positivos frecuentes de las reglas** (refutar con evidencia, no por costumbre):

- Regla de SQL sobre una cadena **constante** o concatenación de constantes (`const`,
  `static readonly` sin entrada externa).
- `Process.Start` con ruta y argumentos **fijos**.
- Código solo invocado desde **pruebas** (`*.Tests`, `[Fact]`, `[Test]`) o herramientas internas
  sin entrada del cliente.
- `Path.Combine` con segmentos que salen de la configuración, no de la petición.
- Secretos "quemados" que son **ejemplos** en `appsettings.Development.json` con valores
  de relleno, o datos sintéticos de pruebas.
- Avisos de CWE genérico (`CWE-20`, `CWE-200`) sin flujo de datos: no se refutan, se
  **reclasifican** a un CWE concreto o se registran como aviso de higiene (Baja).

## Fuentes abiertas

- MITRE CWE — <https://cwe.mitre.org/data/downloads.html>; vistas CWE-1344 (OWASP 2021) y
  CWE-1450 (OWASP 2025 RC1).
- OWASP Top 10 — <https://owasp.org/Top10/>.
- OWASP Risk Rating Methodology — <https://owasp.org/www-community/OWASP_Risk_Rating_Methodology>.
- OWASP ASVS 5.0.0 — <https://github.com/OWASP/ASVS>.
- OWASP Cheat Sheet Series — <https://cheatsheetseries.owasp.org/> (incluye la hoja
  [.NET Security](https://cheatsheetseries.owasp.org/cheatsheets/DotNet_Security_Cheat_Sheet.html)).
- Reglas de seguridad de .NET (`CAxxxx`) — <https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/security-warnings>.
