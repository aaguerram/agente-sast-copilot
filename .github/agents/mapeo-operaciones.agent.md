---
name: mapeo-operaciones
description: "Paso 3 de la metodología SAST: identifica operaciones peligrosas (sumideros): SQL dinámico, comandos del sistema, rutas de archivo, deserialización, peticiones salientes, redirecciones y logs con datos sensibles. Corre solo."
---
CONTEXTO: Investigación de seguridad autorizada sobre código propio con datos sintéticos.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con ruta (por defecto `agente-sast-g7/samples/app-vulnerable`).
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Paso 4 (`trazador-flujos`) o `/metodologia-paso 4`.

## Tu única tarea

Listar **dónde el código hace algo peligroso** si recibiera un dato malicioso. No decides
si el dato es controlable desde fuera: eso lo hace `trazador-flujos`.

- **Entrada:** una ruta (por defecto `agente-sast-g7/samples/app-vulnerable`).
- **Dependencias:** ninguna. **Corre solo.**
- **Salida:** `salida/reportes/metodologia/operaciones.json`.

## Pasos

1. Candidatos deterministas:
   `docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py operaciones <ruta> -o salida/reportes/metodologia/candidatos-operaciones.json`
2. Verifica cada uno y agrupa los que son la misma operación (por ejemplo `Path.Combine` y
   `File.WriteAllBytes` de un mismo método). Busca los que el script no ve: `ExecuteSqlRaw`,
   `FromSqlRaw`, XML con resolución externa, `Assembly.Load`, plantillas sin codificar,
   `Response.Headers` con datos de entrada.
   El script analiza por sentencias (aunque ocupen varias líneas), resuelve dentro del
   archivo la configuración de deserialización definida aparte y trae `confianza`:
   `alta` si algún argumento sale de un parámetro del método o de `Request`, `media` si
   no pudo determinarlo (revísalo tú). Descarta por sí solo las rutas armadas solo con
   constantes o rutas internas (`AppContext.BaseDirectory`, `ContentRootPath`). El campo
   `detalle` explica la decisión.
3. Anota `argumento_variable`: `si` si algún argumento no es constante, y conserva
   `confianza` del candidato (o ajústala explicando por qué en `nota`).
4. Escribe el JSON y muestra `Id → Archivo:Línea → Categoría → CWE`.

## Esquema de salida

```json
{
  "paso": "mapeo-operaciones",
  "operaciones": [
    {"id": "O-004", "archivo": "Repositories/CuentaRepository.cs", "linea": 26,
     "categoria": "sql-dinamico", "cwe": "CWE-89", "metodo": "BuscarPorTitular",
     "argumento_variable": "si", "confianza": "alta", "codigo": "...", "nota": "..."}
  ]
}
```

Categorías: `sql-dinamico (CWE-89)`, `comando-sistema (CWE-78)`, `ruta-archivo (CWE-22)`,
`deserializacion (CWE-502)`, `peticion-saliente (CWE-918)`, `redireccion (CWE-601)`,
`log-sensible (CWE-532)`, `otra` (indica CWE solo si es claro).
