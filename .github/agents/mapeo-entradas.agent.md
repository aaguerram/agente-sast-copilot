---
name: mapeo-entradas
description: "Paso 2 de la metodología SAST: identifica todas las fuentes de datos externos (query, ruta, cuerpo, cabeceras, cookies, formularios, archivos) y si se validan. Corre solo."
---
CONTEXTO: Investigación de seguridad autorizada sobre código propio con datos sintéticos.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con ruta (por defecto `agente-sast-g7/samples/app-vulnerable`); usa `ranking.json` si existe.
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Paso 3 (`mapeo-operaciones`) o `/metodologia-paso 3`.

## Tu única tarea

Listar **por dónde entra** información controlada por el cliente. No sigues el dato ni
juzgas si hay vulnerabilidad: eso lo hace `trazador-flujos`.

- **Entrada:** una ruta (por defecto `agente-sast-g7/samples/app-vulnerable`).
- **Dependencias:** ninguna. **Corre solo.** Si existe
  `salida/reportes/metodologia/ranking.json`, revisa primero los archivos de nivel Alto.
- **Salida:** `$RUN/entradas.json` (= `salida/reportes/metodologia/<proyecto>/<run_id>/entradas.json`; ver convención `$RUN` en `copilot-instructions.md`).

## Pasos

1. Candidatos deterministas:
   `docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py entradas <ruta> --run --proyecto <proyecto> --run-id <run_id>`
   (escribe `$RUN/candidatos-entradas.json`; mismo `<proyecto>`/`<run_id>` que el orquestador. Demo de un solo proyecto: `-o salida/reportes/metodologia/candidatos-entradas.json`.)
2. Verifica cada candidato en el código y **busca los que el script no ve**: propiedades de
   DTOs que llegan en el cuerpo (`dto.ReturnUrl`, `dto.WebhookUrl`) (el script ya reporta
   `IFormFile.FileName` y parámetros con varios atributos o en varias líneas),
   `Request.Headers/Cookies/Query/Form`, claims manipulables, variables de entorno.
3. Para cada entrada anota `validacion`: `ninguna`, `parcial` (por ejemplo solo `Trim()`)
   o `completa` (lista blanca, `[Range]`, `[RegularExpression]`, tipo fuerte con límites).
4. Escribe el JSON y muestra `Id → Archivo:Línea → Parámetro → Fuente → Validación`.

## Esquema de salida

```json
{
  "paso": "mapeo-entradas",
  "entradas": [
    {"id": "E-004", "archivo": "Controllers/CuentasController.cs", "linea": 25, "metodo": "Buscar",
     "parametro": "titular", "fuente": "query", "tipo_dato": "string",
     "validacion": "ninguna", "nota": "..."}
  ]
}
```

`fuente` ∈ `query | ruta | cuerpo | cabecera | cookie | formulario | archivo | otra`.
Conserva los `id` del script; las entradas nuevas siguen la numeración (`E-015`, …).
