---
name: ranking-archivos
description: "Paso 1 de la metodología SAST: puntúa los archivos C# de una ruta por riesgo (Alto/Medio/Bajo) para decidir dónde mirar primero. Corre solo."
---
CONTEXTO: Investigación de seguridad autorizada sobre código propio con datos sintéticos.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con ruta (por defecto `agente-sast-g7/samples/app-vulnerable`).
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Paso 2 (`mapeo-entradas`) o `/metodologia-paso 2`.

## Tu única tarea

Ordenar los archivos `.cs` de la ruta indicada por **riesgo de seguridad**. No buscas
vulnerabilidades concretas: decides el orden de revisión de los pasos siguientes.

- **Entrada:** una ruta. Por defecto `agente-sast-g7/samples/app-vulnerable`.
- **Dependencias:** ninguna. **Corre solo.**
- **Salida:** `salida/reportes/metodologia/ranking.json`.

## Pasos

1. Genera candidatos deterministas (no transcribas a mano):
   `docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py inventario <ruta> -o salida/reportes/metodologia/candidatos-inventario.json`
2. Lee los candidatos y **abre los archivos de nivel Alto y Medio**. Ajusta el nivel con
   criterio, explicándolo en `motivo`:
   - Sube: autenticación, sesión, dinero (transferencias, pagos), SQL, archivos subidos,
     procesos del sistema, red saliente, deserialización, controladores sin `[Authorize]`,
     servicios que deberían aplicar reglas de negocio aunque el regex no los marque.
   - Baja: DTOs, constantes, registro de dependencias sin lógica.
3. Escribe el JSON y muestra la tabla `Posición → Archivo → Nivel → Motivo`.

## Esquema de salida

```json
{
  "paso": "ranking-archivos",
  "ruta": "agente-sast-g7/samples/app-vulnerable",
  "archivos": [
    {"posicion": 1, "archivo": "Controllers/CuentasController.cs", "nivel": "Alto",
     "puntaje": 12, "senales": ["controlador-sin-authorize"], "motivo": "..."}
  ]
}
```

## Reglas

- No inventes archivos: solo los que existen en la ruta.
- El puntaje del script es una pista, no la verdad. Si cambias un nivel, di por qué.
