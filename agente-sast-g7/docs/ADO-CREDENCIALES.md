# Cómo entregar las credenciales de Azure DevOps (de forma segura)

> **Regla de oro:** el PAT de Azure DevOps **no se pega en el chat ni se sube al repo**.
> Las bases del hackathon prohíben secretos en repositorio, logs o documentación. El
> agente nunca necesita el *valor* del token: lo lee desde una variable de entorno.

## Por qué las dos cuentas distintas no son un problema

Son dos canales de autenticación separados:

- **GitHub Copilot** autentica solo el asistente dentro de VS Code. **No** se conecta a
  Azure DevOps.
- **Azure DevOps** se autentica aparte, con un **PAT de la cuenta de ADO**. Quien crea las
  incidencias es el script/pipeline, no Copilot.

Lo único que debes garantizar: que la cuenta de ADO sea miembro del proyecto con permiso
para **crear work items**.

## Lo que SÍ me das (no es secreto)

Pega estos valores en tu archivo `.env` local (copiado de `.env.example`). Puedes
compartirlos aquí porque **no** son secretos:

| Variable | Qué es | Ejemplo |
|---|---|---|
| `ADO_ORG_URL` | URL de la organización de ADO | `https://dev.azure.com/MI_ORG` |
| `ADO_PROJECT` | Nombre del proyecto | `HackaPro-G7` |
| `ADO_WORKITEM_TYPE` | Tipo de work item | `Bug` |
| `ADO_AREA_PATH` / `ADO_ITERATION_PATH` | Opcional, si el proyecto los exige | |

## Lo que NO me das: el PAT

### 1. Crear el PAT (desde la cuenta de Azure DevOps)

1. Inicia sesión en `https://dev.azure.com/TU_ORGANIZACION` **con la cuenta de ADO**
   (la distinta de Copilot).
2. Arriba a la derecha: icono de usuario → **Personal access tokens**.
3. **New Token**.
4. Organización: la correcta. Nombre: `agente-sast-g7`. Expiración: la más corta posible.
5. **Scopes** → *Show all scopes* → **Work Items**: marca **Read, write, & manage**.
   (Si además leerás el repo, añade **Code: Read**.)
6. **Create** y **copia el token una sola vez** (ya no se vuelve a mostrar).

### 2. Guardarlo (elige según dónde corra)

**Local (desarrollo/demo):** pégalo en tu `.env`, que está en `.gitignore`:

```
ADO_PAT=xxxxxxxxxxxxxxxxxxxx
```

**Pipeline de Azure DevOps:** guárdalo como **variable secreta** (Pipelines → Library →
Variable group, o variable del pipeline con el candado). En el YAML se referencia como
`$(ADO_PAT)`, nunca en texto plano.

### 3. Verificar sin exponerlo

```bash
# Carga el .env y prueba la conexión (no imprime el token)
python3 scripts/crear_incidencias_ado.py --self-test
```

## Checklist

- [ ] La cuenta de ADO puede crear work items en el proyecto.
- [ ] PAT con scope **Work Items: Read, write & manage**, expiración corta.
- [ ] PAT en `.env` local o variable secreta del pipeline — **nunca** en el repo ni en el chat.
- [ ] `.env` aparece en `.gitignore` (ya está).
- [ ] Me diste solo `ADO_ORG_URL`, `ADO_PROJECT` y el tipo de work item.
