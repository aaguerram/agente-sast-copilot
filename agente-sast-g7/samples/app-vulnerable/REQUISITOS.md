# Requisitos — Banca en línea del Banco Ficticio (sintético)

Historias de usuario, reglas de negocio y modelo de amenazas que la API **debería**
cumplir. Las usa el paso `analizador-gaps` para comparar el código con la intención.
Todos los datos son ficticios.

## Historias de usuario

| ID | Historia | Criterio de aceptación |
|---|---|---|
| HU-01 | Como cliente quiero ver mis cuentas | Solo se devuelven cuentas cuyo `ClienteId` es el del cliente autenticado. |
| HU-02 | Como cliente quiero buscar una cuenta destino por titular | Requiere sesión; la búsqueda no expone saldos de terceros. |
| HU-03 | Como cliente quiero transferir dinero | El monto es mayor que 0; la cuenta origen es del cliente autenticado. |
| HU-04 | Como cliente quiero subir comprobantes | Solo PDF o imagen, máximo 5 MB, guardados con un nombre generado por el servidor. |
| HU-05 | Como analista quiero exportar reportes | Solo en los formatos `pdf` o `csv`. |
| HU-06 | Como cliente quiero cerrar sesión y volver a la página de inicio | La redirección solo va a rutas del propio sitio. |

## Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | Un cliente **solo** puede ver y operar **sus** cuentas. |
| RN-02 | Las transferencias de **más de 10 000** requieren aprobación de un supervisor antes de ejecutarse. |
| RN-03 | Límite diario de transferencias: **20 000** por cliente. |
| RN-04 | La identidad del cliente sale **del token de autenticación**, nunca de cabeceras, cookies ni del cuerpo de la petición. |
| RN-05 | Todos los endpoints que devuelven datos de clientes requieren autenticación. |
| RN-06 | La auditoría de transferencias no registra claves ni datos de autenticación. |

## Modelo de amenazas (resumen)

| Amenaza | Control esperado |
|---|---|
| Un cliente lee datos de otro cambiando un id (IDOR) | Filtro por cliente autenticado en cada consulta (RN-01). |
| Suplantación cambiando cabeceras o cookies | Identidad solo desde el token (RN-04). |
| Fraude por montos altos o repetidos | Aprobación (RN-02) y límite diario (RN-03). |
| Montos negativos que invierten la transferencia | Validación de monto > 0 (HU-03). |
| Archivos subidos que escapan de su carpeta o son ejecutables | Nombre generado y tipos permitidos (HU-04). |
| Phishing usando el dominio del banco | Redirecciones solo locales (HU-06). |
