# agente-sast-g7 — Análisis de Pruebas SAST (HackaPro 2026)

Cadena de agentes de GitHub Copilot que **consume** reportes SAST, los normaliza, prioriza,
propone remediación, filtra falsos positivos y crea incidencias en **Azure DevOps**.
Grupo 7 del reto. **Fortify sigue siendo la herramienta SAST oficial**; estos agentes la
complementan, no la reemplazan.

## Stack

- **GitHub Copilot (VS Code)** — agentes custom en `.github/agents/` **de la raíz del repo**
  (Copilot solo carga `.github/` de la raíz del espacio de trabajo) + skill `/sast`.
- **Semgrep CE** — genera los reportes SARIF en el sandbox (Fortify el día de la demo).
- **.NET / C#** — lenguaje objetivo.
- **Azure DevOps Boards** — destino de las incidencias.

> **Metodología SAST paso a paso** (entradas, proceso, validación, salidas y ejemplos):
> [`METODOLOGIA.md`](METODOLOGIA.md).

## Estructura

```
../.github/                   (en la raíz del repo)
  copilot-instructions.md     Reglas del repo para Copilot
  agents/                     receptor, priorizador, remediador, devils-advocate, orquestador-pruebas,
                              metodologia-sast + ranking-archivos, mapeo-entradas, mapeo-operaciones,
                              trazador-flujos, analizador-gaps
  skills/                     /ayuda, /demo, /sast [reporte.sarif], /validar-local, /replicar-ado,
                              /metodologia [ruta], /metodologia-paso <paso> [ruta]
  prompts/                    compatibilidad con VS Code anterior: remiten a la skill del mismo nombre
scripts/
  normalizar_sarif.py         SARIF → JSON común
  crear_incidencias_ado.py    JSON validado → work items (dedup, Human-in-the-Loop)
  metodologia.py              Candidatos deterministas de la metodología (inventario, entradas, operaciones)
  comparar_esperado.py        Compara los resultados con la referencia samples/app-vulnerable/esperado/
  tests/test_metodologia.py   Pruebas del script y de la ejecución de referencia
samples/codigo-dotnet/        Código C# vulnerable para demos (sintético)
samples/app-vulnerable/       API .NET sintética con fallas en todas las capas + REQUISITOS.md
                              y esperado/ (respuesta de referencia de cada paso)
azure-pipelines.yml           Semgrep → normalizar → incidencias
docs/ADO-CREDENCIALES.md      Cómo entregar credenciales de ADO de forma segura
```

## Flujo

1. **Recepción** — `normalizar_sarif.py` valida y normaliza el reporte.
2. **Priorización** — agente `priorizador-cwe-owasp` (CWE, OWASP, prioridad).
3. **Remediación** — agente `remediador` propone correcciones (no toca el código).
4. **Validación adversarial** — agente `devils-advocate` refuta falsos positivos.
5. **Incidencias** — `crear_incidencias_ado.py` crea work items Crítica/Alta, sin duplicar.

## Primeros pasos

Todo corre con Docker desde la **raíz del repo** (no se instala nada):

```bash
cp agente-sast-g7/.env.example agente-sast-g7/.env   # ADO_ORG_URL, ADO_PROJECT (el PAT va aparte)
# Ver docs/ADO-CREDENCIALES.md para el PAT (no se pega en el chat ni se versiona)

./scripts/validar-local.sh --solo semgrep-demo        # salida/reportes/semgrep-muestras.sarif

# En VS Code con Copilot (abriendo la raíz del repo):  /sast salida/reportes/semgrep-muestras.sarif
docker compose --profile agentes run --rm py \
  agente-sast-g7/scripts/crear_incidencias_ado.py salida/reportes/validado.json --dry-run
```

## Seguridad (reglas del hackathon)

- Secretos solo en variables de entorno / variables secretas del pipeline. Nunca en repo,
  logs, reportes ni prompts.
- Solo datos sintéticos.
- Human-in-the-Loop: las correcciones sugeridas las revisa una persona; el agente registra
  incidencias, no parchea el código automáticamente.
