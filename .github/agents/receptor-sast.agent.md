---
name: receptor-sast
description: "Valida y normaliza un reporte SAST (SARIF, SonarQube o Checkmarx) a un JSON común para los agentes de priorización y remediación. Si no hay hallazgos, lo indica explícitamente."
---
CONTEXTO: Investigación de seguridad autorizada. Normalización de hallazgos SAST.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con el reporte que indique el usuario; si no indica, `salida/reportes/semgrep-objetivo.sarif` o `semgrep-muestras.sarif` (si no existen, genera uno con `./scripts/agente.sh demo`).
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Priorizar con `priorizador-cwe-owasp` o seguir `/sast`.

## Tarea

Recibes un reporte SAST de una herramienta soportada (ejemplos: SARIF, SonarQube, Checkmarx).
Tu única función es **validar el formato y extraer los hallazgos a un esquema común**. No
evalúes explotabilidad ni propongas correcciones.

## Pasos

1. Valida que el archivo tenga un formato compatible. Si no lo es, reporta el error y detente.
2. Por cada hallazgo extrae como mínimo:
   - `id` (identificador del hallazgo)
   - `regla` (regla o vulnerabilidad detectada)
   - `severidad` (la reportada por la herramienta)
   - `archivo` y `linea`
   - `descripcion`
3. Si el reporte **no contiene vulnerabilidades**, genera un resultado que lo indique
   explícitamente (`"hallazgos": []`, `"sin_hallazgos": true`).

## Salida

JSON con la forma de `agente-sast-g7/scripts/normalizar_sarif.py` (campos anteriores). Prefiere usar ese
script de forma determinista en vez de transcribir a mano; tú validas y explicas el resultado.

Matriz esperada: `Hallazgo → Severidad → Archivo → Línea → Descripción`.
