# SSDLC: ciclo de vida de desarrollo seguro

## Qué es

El **Secure Software Development Life Cycle** (Secure SDLC o SSDLC) es el ciclo de desarrollo
de software de siempre, con actividades de seguridad integradas en cada fase en lugar de una
revisión única al final.

## Por qué importa

- **Cuesta menos:** un fallo detectado en diseño es mucho más barato de corregir que uno en producción.
- **Reduce el riesgo:** llegan menos vulnerabilidades a producción.
- **Facilita el cumplimiento:** deja evidencia para auditorías y normas (ISO 27001, PCI DSS).

## Seguridad en cada fase

| Fase | Actividad de seguridad |
|------|------------------------|
| Requisitos | Requisitos de seguridad y de cumplimiento, junto a los funcionales |
| Diseño | Modelado de amenazas y revisión de arquitectura |
| Desarrollo | Código seguro, revisión de código, análisis estático (SAST) y de dependencias (SCA) |
| Pruebas | Análisis dinámico (DAST) y pruebas de penetración |
| Despliegue | Configuración endurecida, gestión de secretos, escaneo de imágenes e infraestructura |
| Operación | Monitoreo, parches y respuesta a incidentes |

## Principios

- **Shift left:** mover la seguridad lo más temprano posible en el ciclo.
- **Automatizar:** los controles corren en el pipeline de CI/CD, no dependen de que alguien se acuerde.
- **Responsabilidad compartida:** la seguridad es de todo el equipo, no solo del área de seguridad.

## Marcos de referencia

- [NIST SSDF (SP 800-218)](https://csrc.nist.gov/projects/ssdf)
- [OWASP SAMM](https://owaspsamm.org/)
- [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl)
