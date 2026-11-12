# Hooks de pre-commit para .NET

Quince reglas propias de buenas prácticas para .NET que corren en **pre-commit**, antes de
que el código llegue al repositorio. Viven en `tools/pre-commit-hooks/` (Python, solo
biblioteca estándar) y se registran como `repo: local` en `.pre-commit-config.yaml`, así que
el job `pre_commit` del pipeline las ejecuta sin cambios.

## Por qué hacen falta si ya está SonarQube Community

Se verificó contra un SonarQube Community **26.11** (perfil por defecto *Sonar way*, 121 de
456 reglas C# activas, 30 reglas de secretos):

1. **No lee la configuración de .NET.** El analizador de secretos solo revisa
   `*.sh, *.properties, *.conf, *.config, *.env, *.pem, *.key…`: **no** `appsettings*.json`.
   Tampoco hay reglas para `.csproj` (versiones de NuGet) ni para `AllowedHosts`.
2. **No tiene análisis de flujo (taint).** Las reglas de inyección SQL, de comandos o
   SSRF (`S3649`, `S2076`, `S5144`) **no existen** en Community: son de Developer Edition en
   adelante. Ese hueco lo cubre Semgrep, no estos hooks.
3. **Llega tarde.** Sonar analiza en el pipeline, después del *push*: un secreto ya quedó
   en el historial y hay que rotarlo. pre-commit lo frena en la máquina del desarrollador.
4. **No bloquea lo que sí detecta.** El pipeline corta solo con `BLOCKER`/`CRITICAL`
   (`SONAR_FAIL_ON`). Reglas que Sonar tiene activas pero con severidad menor —URI
   quemada `S1075` (MINOR), credenciales `S2068` (MAJOR), CORS `S5122` (MAJOR), modo
   depuración `S4507` (MINOR), PRNG `S2245` (MAJOR)— no detienen el PR.
5. **Reglas que existen pero están apagadas:** bloqueo síncrono de `async` (`S4462`) y
   control de supresiones (`S1309`) vienen inactivas. Deserialización con `BinaryFormatter`
   o `TypeNameHandling` no tiene regla en Sonar; los analizadores de Microsoft
   (`CA2300`–`CA2330`) existen pero están deshabilitados por defecto.

## Reglas

**Bloquea** = el commit (y el PR) no pasa. **Avisa** = se muestra pero no detiene.

| Hook | Detecta | Modo | Referencia | Hueco que cubre frente a Sonar Community |
|---|---|---|---|---|
| `dotnet-url-quemada` | URL (`http`, `amqp`, `redis`…) o IP en un literal de C#. Ignora comentarios, espacios de nombres XML, URLs con host dinámico y `localhost` en proyectos de pruebas | Bloquea | ASVS 5.0 V13 · CWE-547 · 12-Factor III | `S1075`/`S1313` son MINOR: no bloquean |
| `dotnet-credencial-quemada` | Cadenas de conexión con `Password=`/`AccountKey=`, URLs con usuario y clave, y asignaciones a `*Password`, `*Secret`, `*ApiKey`, `*Token`… con valor real | Bloquea | ASVS 5.0 V13.3 · CWE-798 | `S2068` es MAJOR; se detiene antes del historial |
| `dotnet-secreto-en-config` | Secretos con valor real en `appsettings*.json` (excepto `Development`) | Bloquea | ASVS 5.0 V13.3 · CWE-798/260 | Sonar no analiza `appsettings*.json` |
| `dotnet-tls-sin-validar` | `ServerCertificateCustomValidationCallback => true`, `DangerousAcceptAnyServerCertificateValidator`, SSL3/TLS 1.0/1.1, CRL desactivada | Bloquea | ASVS 5.0 V12 · CWE-295/326 | Sonar lo tiene (`S4830`, `S4423`); aquí se frena antes del push |
| `dotnet-cors-inseguro` | Origen abierto (`AllowAnyOrigin`, `SetIsOriginAllowed(_ => true)`, `"*"`) + `AllowCredentials()` en la misma política | Bloquea | ASVS 5.0 V3 · CWE-942 | `S5122` es MAJOR: no bloquea |
| `dotnet-developer-exception-page` | `UseDeveloperExceptionPage()` fuera de `if (…IsDevelopment())` | Bloquea | ASVS 5.0 V16 · CWE-209/489 | `S4507` es MINOR: no bloquea |
| `dotnet-deserializacion-insegura` | `BinaryFormatter`, `SoapFormatter`, `NetDataContractSerializer`, `LosFormatter`, `TypeNameHandling` ≠ `None` | Bloquea | ASVS 5.0 V1 · CWE-502 · CA2300-2330 | Sin regla en Sonar; CA23xx apagadas por defecto |
| `dotnet-hash-debil` | `MD5`, `SHA1`, `HMACMD5`, `HMACSHA1`, `HashAlgorithmName.MD5/SHA1` | Bloquea | ASVS 5.0 V11 · CWE-327/328 | Sonar lo tiene (`S4790`); aquí se frena antes del push |
| `dotnet-random-inseguro` | `new Random()` / `Random.Shared` en un miembro que habla de token, salt, OTP, contraseña… | Bloquea | ASVS 5.0 V11 · CWE-338 · CA5394 | `S2245` es MAJOR: no bloquea |
| `dotnet-supresion-sin-justificar` | `#pragma warning disable` sin comentario y `[SuppressMessage]` sin `Justification` | Bloquea | Analizadores CA/IDE de Microsoft | `S1309` inactiva por defecto |
| `dotnet-paquete-version-flotante` | `Version="*"`, `"10.*"` en `PackageReference`/`PackageVersion` | Bloquea | ASVS 5.0 V15 · CWE-1357/829 · OWASP Top 10 2025 A03 | Sonar no revisa `.csproj` |
| `dotnet-swagger-sin-entorno` | `UseSwagger`, `UseSwaggerUI`, `MapOpenApi` sin chequeo de entorno | Avisa | ASVS 5.0 V13 · CWE-200 · OWASP API9:2023 | Sin regla en Sonar |
| `dotnet-allowed-hosts-comodin` | `"AllowedHosts": "*"` fuera de `Development` | Avisa | ASVS 5.0 V13 · CWE-644 | Sonar no analiza `appsettings*.json` |
| `dotnet-catch-vacio` | `catch { }` sin ningún comentario dentro | Avisa | CWE-390 · CA1031 | Sonar lo tiene (`S108`, `S2486`) sin bloquear |
| `dotnet-async-bloqueante` | `.Wait()`, `.GetAwaiter().GetResult()`, `…Async(…).Result` | Avisa | CWE-833 · VSTHRD002 | `S4462` inactiva por defecto |

Las fuentes de la tabla: [OWASP ASVS 5.0](https://github.com/OWASP/ASVS),
[OWASP .NET Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DotNet_Security_Cheat_Sheet.html),
[CWE](https://cwe.mitre.org/), [analizadores de calidad de código de .NET](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/),
[The Twelve-Factor App — III. Config](https://12factor.net/config) y
[reglas C# de Sonar](https://rules.sonarsource.com/csharp/).

## Ejecutar

Todo corre en contenedores; no hay que instalar nada:

```bash
docker compose --profile seguridad run --rm pre-commit              # todos los hooks
docker compose --profile seguridad run --rm pre-commit-hooks-tests  # pruebas de las reglas
docker compose --profile seguridad run --rm pre-commit-hooks-tests \
  python tools/pre-commit-hooks/dotnet_buenas_practicas.py --listar  # catálogo
```

## Aceptar un hallazgo

Cuando el hallazgo es intencional, se deja escrito el motivo (sin motivo no cuenta):

=== "C# / .csproj"

    ```csharp
    // pre-commit:allow dotnet-hash-debil ETag de compatibilidad con el CDN, no es seguridad
    var etag = MD5.HashData(contenido);
    ```

=== "JSON (no admite comentarios)"

    Una línea en `tools/pre-commit-hooks/permitidos.txt`:

    ```text
    dotnet-allowed-hosts-comodin rickmorty-clean/src/RickMorty.Api/appsettings.json La API se publica detrás de un gateway que filtra el Host
    ```

## Pruebas

`tools/pre-commit-hooks/tests/fixtures/` tiene, por tipo de archivo, un caso `positivo`
(cada línea marcada con `ESPERA <id>` debe disparar esa regla) y uno `negativo` (no debe
disparar nada). La prueba compara el conjunto exacto de (regla, línea), así que detecta
tanto falsos positivos como falsos negativos, y exige un caso positivo por regla. Los
fixtures están excluidos de pre-commit, Semgrep y gitleaks porque son inseguros a propósito.

## Limitaciones

- Son reglas de **texto y léxico**, no de flujo de datos: no siguen un valor entre métodos
  ni archivos. `dotnet-random-inseguro` y los chequeos de entorno usan heurísticas de
  contexto (nombre del miembro, líneas previas) y pueden fallar en código atípico.
- Un `else` que publique Swagger o la página de errores después de un `if
  (IsDevelopment())` no se detecta.
- `dotnet-secreto-en-config` decide por el **nombre** de la clave (o por `Password=` en el
  valor). Un secreto con una clave neutra (`"Valor": "…"`) lo debe atrapar gitleaks.
- No sustituyen el análisis de dependencias vulnerables (`dotnet list package
  --vulnerable`), que necesita restaurar paquetes y no encaja en un hook rápido.
