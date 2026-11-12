---
name: trazador-flujos
description: "Paso 4 de la metodología SAST: une entradas y operaciones peligrosas siguiendo el dato entre archivos y capas (Controller → Service → Repository) y registra el saneamiento que encuentre. Depende de los pasos 2 y 3."
---
CONTEXTO: Investigación de seguridad autorizada sobre código propio con datos sintéticos.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con `entradas.json` y `operaciones.json` de `salida/reportes/metodologia/` (si faltan, ofrece generarlos con los pasos 2 y 3); ruta por defecto `agente-sast-g7/samples/app-vulnerable`.
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Paso 6 (`devils-advocate`) o `/metodologia-paso 6`.

## Tu única tarea

Responder, para cada operación peligrosa: **¿le puede llegar un dato del cliente?**
Siguiendo el dato desde la entrada hasta la operación, aunque cruce varios archivos.
Esto es lo que SonarQube Community no hace (análisis *taint* entre funciones).

- **Dependencias:** `salida/reportes/metodologia/entradas.json` (paso 2) y
  `operaciones.json` (paso 3). **No corre solo.** Si falta alguno, ejecuta antes ese paso
  (`mapeo-entradas` / `mapeo-operaciones`, o pide al usuario que lo haga) y luego sigue.
- **Salida:** `salida/reportes/metodologia/flujos.json`.

## Pasos

1. Para cada operación de `operaciones.json`, sube por la cadena de llamadas: método que la
   contiene → quién lo llama (busca el nombre del método en la ruta) → … hasta una entrada
   de `entradas.json` o hasta una constante.
2. Registra cada salto en `camino` con archivo, línea y símbolo.
3. Revisa el **saneamiento** en cada salto: lista blanca, conversión a tipo fuerte,
   parametrización, `LocalRedirect`/`Url.IsLocalUrl`, `Path.GetFileName` + comprobación de
   carpeta, etc. `saneamiento` ∈ `ninguno | parcial | completo`, con `detalle`.
   - Un flujo con saneamiento `completo` **se reporta igual** (con esa marca): lo decide
     `devils-advocate`. No lo descartes tú.
4. Operaciones sin entrada que les llegue: no generan flujo (anótalas en `sin_flujo`).
5. Escribe el JSON y muestra `Id → Fuente → Sumidero → Archivos cruzados → Saneamiento`.

## Esquema de salida

```json
{
  "paso": "trazador-flujos",
  "flujos": [
    {"id": "F-01", "titulo": "Inyección SQL en búsqueda por titular", "cwe": "CWE-89",
     "fuente": "E-004", "sumidero": "O-004",
     "camino": [
       {"archivo": "Controllers/CuentasController.cs", "linea": 25, "simbolo": "Buscar(titular)", "nota": "query sin validar"},
       {"archivo": "Services/CuentaService.cs", "linea": 18, "simbolo": "BuscarPorTitular", "nota": "solo Trim()"},
       {"archivo": "Repositories/CuentaRepository.cs", "linea": 26, "simbolo": "BuscarPorTitular", "nota": "concatenación en LIKE"}
     ],
     "saneamiento": "parcial", "detalle": "Trim() no neutraliza comillas", "estado": "candidato"}
  ],
  "sin_flujo": [{"operacion": "O-0xx", "motivo": "argumento constante"}]
}
```

## Reglas

- Cada salto debe existir en el código (archivo:línea verificables). Si no puedes cerrar
  el camino, marca `estado: "incompleto"` y explica dónde se corta.
- No escribas pruebas de explotación ni cargas maliciosas: describe el riesgo.
