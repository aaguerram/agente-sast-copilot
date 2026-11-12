# Recomendaciones: reutilización de agentes de terceros

Análisis de dos repositorios públicos como posible base para el **Grupo 7 · Análisis
de Pruebas SAST** de [HackaPro 2026](hackapro.md), alineado con el [SSDLC](ssdlc.md).

## Repositorios evaluados

| Repositorio | Qué es | Licencia |
|---|---|---|
| [H-mmer/pentest-agents](https://github.com/H-mmer/pentest-agents) | Framework de bug bounty ofensivo para Claude Code y 6 herramientas más (~50 agentes, comandos, skills y 2 servidores MCP). Incluye un subconjunto de agentes **SAST**. | MIT |
| [evyatarmeged/Raccoon](https://github.com/evyatarmeged/Raccoon) | Herramienta de reconocimiento e *information gathering* (DNS, WHOIS, TLS, escaneo de puertos, fuzzing, enumeración de subdominios, detección de WAF). | MIT |

## Veredicto

!!! success "pentest-agents — útil como patrón de diseño, no como producto a entregar"
    Su pipeline **SAST** aporta una arquitectura directamente aplicable al Grupo 7.
    No se reutilizan sus módulos ofensivos ni sus servidores MCP externos.

!!! failure "Raccoon — no aplica a este reto"
    Es recon de red contra sistemas en producción (escaneo de puertos, enumeración de
    subdominios, fuzzing). No tiene relación con analizar hallazgos SAST ni con el
    pipeline del SSDLC, y usarlo contra infraestructura del banco chocaría con las
    reglas del hackathon (solo sandbox, datos sintéticos, nada contra sistemas reales).

## Qué reutilizar de pentest-agents

El valor está en el **patrón de arquitectura**, no en los exploits:

- **Razonamiento descompuesto** (`skills/sast-methodology`): en vez de pedir a un solo
  agente "encuentra vulnerabilidades" (que alucina hallazgos plausibles pero falsos),
  se descompone en pasos enfocados:

    ```
    Ranking de archivos → Mapeo de entradas → Mapeo de operaciones peligrosas
        → Trazado de flujos → Análisis de gaps → Validación adversarial → PoC
    ```

- **Validador adversarial** (agente *devil's advocate*): un agente cuyo único trabajo es
  **refutar** cada hallazgo. Ataca el punto débil que las bases no mencionan —los
  **falsos positivos** del SAST— y es un diferenciador real en los criterios de
  *Calidad de IA* e *Innovación*.

- **Combinar herramientas deterministas + IA**: ejecutar análisis estático
  (p. ej. Semgrep/CodeQL), luego enriquecer y deduplicar con el agente. Refuerza el
  requisito del reto de que **Fortify siga siendo la herramienta oficial** y los
  agentes la *complementen*, no la reemplacen.

### Mapeo a las piezas del Grupo 7

| Pieza del reto | Patrón reutilizable |
|---|---|
| Recepción / normalización de resultados SAST | Parseo de warnings estáticos a un JSON común |
| Priorización según CWE / OWASP | *File-ranker* y ordenamiento por severidad |
| Sugerencia de correcciones seguras | Cadena *flow-tracer* + *gap-analyzer*, orientada a remediación (no a exploit) |
| Registro automático / control de calidad | Validador *devil's advocate* antes de crear incidencias |

### Estado de implementación en este repo

| Patrón | Estado |
|---|---|
| Validador adversarial | Implementado: agente `devils-advocate` |
| Herramientas deterministas + IA | Implementado: Semgrep, SonarQube o Fortify generan SARIF que consume `/sast`; `metodologia.py` genera candidatos para los agentes |
| Normalizar, priorizar y proponer corrección | Implementado: `receptor-sast` → `priorizador-cwe-owasp` → `remediador` |
| Ranking de archivos, mapeo de entradas y operaciones, trazado de flujos, análisis de gaps | Implementado como agentes de Copilot orquestados por `metodologia-sast` ([Metodología SAST](metodologia-sast.md)) |
| Prueba de explotación (PoC) | No se implementa: el Grupo 7 es defensivo |

## Advertencias antes de reutilizar

1. **Licencia e inventario.** Ambos son MIT, pero las bases exigen declarar **todo
   componente de terceros con su licencia** y un inventario de activos preexistentes.
   Lo que se tome debe declararse desde el inicio como activo preexistente.
2. **Solo herramientas aprobadas.** El reto prohíbe cargar información corporativa en
   servicios no autorizados. Los servidores MCP de pentest-agents se conectan a
   plataformas externas de bug bounty: **no** pueden apuntar al código del banco sin
   aprobación.
3. **Lo ofensivo no es el reto.** El grueso de pentest-agents (y todo Raccoon) ataca
   sistemas en vivo. El Grupo 7 es **defensivo**: consume reportes SAST y propone
   correcciones dentro del pipeline. Usar las partes ofensivas contra infraestructura
   del banco violaría las reglas y solo sería legítimo con autorización explícita.

## Pipeline de seguridad por etapa (herramientas open source)

Cadena de controles *shift-left* con herramientas open source, dejando la licencia del
banco solo donde es imprescindible. Sirve como evidencia de SSDLC completo para el
*documento de arquitectura* y el pitch.

| Etapa | Control | Herramienta | Licencia | Bloquea |
|---|---|---|---|---|
| Commit | Secretos | gitleaks | Open source | Sí |
| Commit | URLs y valores quemados | Semgrep CE (reglas propias) | Open source | Sí |
| Pre-push | SAST local | Semgrep CE | Open source | Aviso |
| Pre-push | Dependencias (SCA) | Trivy fs | Open source | Aviso |
| Pull request | Secret scanning (gate en CI) | gitleaks | Open source | Sí |
| Pull request | SAST y quality gate | Semgrep CE | Open source | Sí |
| Pull request | SAST rama principal | SonarQube Community | Open source | Aviso |
| Pull request | Dependencias (SCA) | OWASP Dependency-Check · Trivy | Open source | Crítica y alta |
| Pull request | Licencias OSS (SBOM) | Trivy | Open source | Aviso |
| Pase a UAT | Imagen de contenedor | Trivy | Open source | Crítica |
| Pase a UAT | DAST OWASP Top 10 | OWASP ZAP (Docker) | Open source | Alta |
| Producción | **SAST oficial (entrada del agente G7)** | Fortify · SonarQube del banco | Licencia del banco | Crítica y alta |
| Producción | SCA continuo (SBOM) | OWASP Dependency-Track | Open source | Alerta |

!!! note "Correcciones aplicadas respecto a la propuesta inicial"
    - **Fortify se reposiciona como entrada principal del Grupo 7**, no como control de
      última milla: las bases lo definen como la herramienta SAST **oficial** y el agente
      consume sus reportes.
    - **El *quality gate* por PR lo da Semgrep CE**, no SonarQube Community: la edición CE
      **no analiza por rama ni decora pull requests** (eso requiere Developer Edition), por
      lo que SonarQube queda para la rama principal.
    - **Secret scanning también como gate en CI/PR**: los hooks de commit en cliente se
      pueden saltar; el control real corre en el pipeline.
    - **Se añade control de licencias OSS (SBOM)**: el reto exige inventario de componentes
      de terceros y sus licencias.
    - **Se consolida el SCA**: Trivy/OSV-Scanner/Dependency-Check se solapan; para el MVP,
      un escáner por etapa (Trivy en pipeline + Dependency-Track en operación).

### A qué grupo del reto pertenece cada herramienta

| Grupo del reto | Herramientas |
|---|---|
| Grupo 7 · SAST (entrada del agente) | **Fortify** (oficial), Semgrep CE, SonarQube Community — las tres emiten **SARIF** |
| Grupo 6 · Dependencias (SCA) | Trivy, OSV-Scanner, OWASP Dependency-Check, Dependency-Track |
| Grupo 10 · Pruebas (DAST) | OWASP ZAP |

!!! tip "Para construir el agente del Grupo 7"
    Si el agente parte de **SARIF normalizado**, acepta de una vez Fortify, Semgrep y
    SonarQube. En el sandbox, usar **Semgrep CE → SARIF** como generador de reportes reales
    (gratis) para las dos demos obligatorias —uno con hallazgos y uno limpio— sin depender
    de la licencia de Fortify, que se enchufa el día de la demo.

## Reparto de trabajo: pre-commit, SonarQube Community y el agente

El criterio es que **pre-commit y SonarQube Community detectan patrones** y **el agente
hace lo que requiere entender el código y su contexto**. Si el agente solo vuelve a
encontrar lo que ya da una regla, no aporta nada al reto.

### Qué se queda en las herramientas deterministas

| Capa | Lo que valida bien | Por qué no conviene dárselo al agente |
|---|---|---|
| Pre-commit (gitleaks, linters, formato) | Secretos, formato, sintaxis, archivos grandes, convención de mensajes | Es determinista, tarda segundos y bloquea antes de que el código salga de la máquina. Un agente es lento, cuesta por uso y puede responder distinto en cada ejecución. |
| SonarQube Community | Bugs y *code smells* por regla, *hotspots* de seguridad, duplicación, complejidad, cobertura, historial de deuda | Resultado repetible y auditable, con la misma regla para todos los equipos. |

### Qué hace el agente que ninguna de las dos puede

| # | Capacidad del agente | Límite de pre-commit y SonarQube Community |
|---|---|---|
| 1 | **Descartar falsos positivos con razonamiento**: decide si el hallazgo es explotable (si el dato viene de una entrada externa, si ya hay una validación antes, si el código es alcanzable). | Solo marcan el patrón; no evalúan si es explotable. |
| 2 | **Seguir el dato entre archivos y capas**, desde el *controller* hasta la consulta. | La edición Community no incluye análisis de flujo de datos (*taint*) entre funciones y archivos; está en las ediciones de pago. |
| 3 | **Fallas de lógica de negocio y autorización**: un endpoint que devuelve datos de otro cliente, un flujo que se salta una aprobación, un límite de monto que no se verifica. | No existe regla, porque depende de qué debería hacer el sistema. |
| 4 | **Priorizar por contexto**: el mismo hallazgo es crítico en un servicio expuesto con datos de clientes y menor en una herramienta interna. | Severidad fija por regla. |
| 5 | **Correlacionar y deduplicar entre herramientas**: une lo que Fortify, Semgrep y SonarQube reportan por separado y agrupa alertas con la misma causa raíz. | Cada herramienta solo conoce sus propios hallazgos. |
| 6 | **Proponer la corrección concreta**: un parche adaptado a ese código y sus convenciones, con la explicación para el desarrollador. | Texto genérico de la regla. |
| 7 | **Contrastar contra la intención**: compara el código con el requisito, la historia de usuario o el modelo de amenazas y señala el control que falta. | Solo analizan el código que existe, no el que debería existir. |
| 8 | **Explicar en lenguaje de negocio**: traduce el hallazgo a impacto y a evidencia para auditoría. | Reportan en términos técnicos de la regla. |

### Cómo aplicarlo en el reto

- **Lo que se expresa como regla o expresión regular va a pre-commit o SonarQube**, no al
  agente.
- **Sobre el reporte SARIF**, el agente hace los puntos 1, 4, 5 y 6. Encaja con el
  requisito de que Fortify siga siendo la herramienta oficial y el agente la complemente.
- **Los puntos 2, 3 y 7 son hallazgos nuevos** que ninguna herramienta dio. Son los más
  vistosos para la demo, pero también donde un agente inventa más: cada uno debe pasar por
  el validador *devil's advocate* antes de reportarse.

!!! warning "El agente no reemplaza el bloqueo"
    Como su resultado puede variar entre ejecuciones, lo que impide el commit o el *merge*
    debe seguir siendo la herramienta determinista. El agente opina, prioriza y propone.

## Recomendación

Tomar de **pentest-agents** únicamente el patrón de diseño —*pipeline* descompuesto más
el agente *devil's advocate* para falsos positivos— y reimplementarlo sobre el stack
obligatorio (Azure AI Foundry, GitHub Copilot, Azure DevOps) consumiendo reportes de
**Fortify**. Eso da un diferenciador fundamentado sin arrastrar dependencias ofensivas
ni MCP externos. **Descartar Raccoon** para este reto.
