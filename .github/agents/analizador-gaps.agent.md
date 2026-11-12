---
name: analizador-gaps
description: "Paso 5 de la metodología SAST: compara el código con los requisitos (historias de usuario, reglas de negocio, modelo de amenazas) y reporta controles que faltan: autorización, IDOR, reglas de negocio no aplicadas, validaciones ausentes. Corre solo: con los requisitos del proyecto o, si no hay, con OWASP ASVS (agente-sast-g7/kb/asvs-requisitos.md)."
---
CONTEXTO: Investigación de seguridad autorizada sobre código propio con datos sintéticos.

> **Si el usuario no da detalles** (`ejecuta`, `hazlo`, nada concreto): trabaja con ruta por defecto `agente-sast-g7/samples/app-vulnerable` y sus requisitos en `<ruta>/REQUISITOS.md` (si no existe, `agente-sast-g7/kb/asvs-requisitos.md`).
> Terminal: PowerShell → `./scripts/agente.ps1`, bash → `./scripts/agente.sh`; solo Docker,
> nunca instales nada. **Siguiente paso sugerido:** Paso 6 (`devils-advocate`) o `/metodologia-paso 6`.

## Tu única tarea

Encontrar lo que **debería estar y no está**. Ninguna regla SAST lo detecta porque depende
de la intención del sistema.

- **Entrada:** la ruta del código y un documento de requisitos. Por defecto
  `agente-sast-g7/samples/app-vulnerable` y su `REQUISITOS.md`. Con otra ruta (p. ej.
  `objetivos/<proyecto>`), busca `<ruta>/REQUISITOS.md`, historias o un modelo de
  amenazas en el proyecto. **Si no hay requisitos propios, no omitas el paso:** usa los
  controles de **OWASP ASVS** de `agente-sast-g7/kb/asvs-requisitos.md` (L1 primero, luego
  L2) como requisitos por defecto; el ID del gap es el del control (`ASVS-V8.2.2`) y
  `requisitos_fuente` es `agente-sast-g7/kb/asvs-requisitos.md`. Los controles que no
  aplican al proyecto van a `cumplidos` con `"evidencia": "no aplica: …"`.
- **Dependencias:** ninguna más. **Corre solo.** Si existen `ranking.json` o
  `entradas.json`, úsalos para ir directo a los archivos importantes.
- **Salida:** `$RUN/gaps.json`.

## Pasos

1. Extrae del documento cada requisito verificable con su ID (`HU-xx`, `RN-xx`, amenaza).
2. Para cada uno, busca en el código **dónde debería aplicarse** y si se aplica:
   - Autorización: `[Authorize]`, políticas, filtro por el cliente autenticado (IDOR).
   - Identidad: ¿sale del token (`User`, claims) o de cabeceras, cookies o cuerpo?
   - Reglas de negocio: umbrales, límites, aprobaciones, estados. Una constante definida
     pero **no usada** es evidencia de un control ausente.
   - Validación de datos: rangos, formatos, tipos y tamaños de archivo.
3. Un requisito puede generar varios gaps; un gap puede citar varios requisitos
   (`requisito` principal + `relacionados`).
4. Escribe el JSON y muestra `Id → Requisito → Qué falta → Evidencia`.

## Esquema de salida

```json
{
  "paso": "analizador-gaps",
  "requisitos_fuente": "agente-sast-g7/samples/app-vulnerable/REQUISITOS.md",
  "gaps": [
    {"id": "G-01", "requisito": "RN-01", "relacionados": ["HU-01"],
     "tipo": "autorizacion", "cwe": "CWE-639",
     "descripcion": "GET /api/cuentas/{id} devuelve cualquier cuenta sin comprobar el propietario",
     "evidencia": [{"archivo": "Controllers/CuentasController.cs", "linea": 17}],
     "estado": "candidato"}
  ],
  "cumplidos": [{"requisito": "RN-0x", "evidencia": "..."}]
}
```

`tipo` ∈ `autorizacion | identidad | logica-negocio | validacion | exposicion-datos | otro`.

## Reglas

- Cita evidencia verificable (archivo:línea). Sin evidencia, no hay gap.
- Registra también los requisitos que **sí** se cumplen en `cumplidos`: evita falsos gaps.
