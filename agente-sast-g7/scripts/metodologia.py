#!/usr/bin/env python3
"""Candidatos deterministas para la metodología SAST descompuesta (Grupo 7).

Genera, con heurísticas sobre C#, los candidatos que luego razonan los agentes de
Copilot. No decide si algo es vulnerable: solo lista dónde mirar y con qué confianza.
Solo usa la biblioteca estándar.

    metodologia.py inventario  <ruta> [-o archivo.json]   # paso 1: ranking de archivos
    metodologia.py entradas    <ruta> [-o archivo.json]   # paso 2: fuentes de datos externos
    metodologia.py operaciones <ruta> [-o archivo.json]   # paso 3: operaciones peligrosas
    metodologia.py todo        <ruta> [--dir carpeta]     # los tres, en candidatos-*.json

En el repo se ejecuta en contenedor:
    docker compose --profile agentes run --rm py agente-sast-g7/scripts/metodologia.py todo \\
        agente-sast-g7/samples/app-vulnerable --dir salida/reportes/metodologia

Cómo analiza (paso 3):
  - Por SENTENCIAS, no por líneas: quita comentarios respetando cadenas y une cada
    sentencia hasta ';' o '{' aunque ocupe varias líneas. La línea reportada es la del
    inicio de la coincidencia en el archivo original.
  - Resuelve dentro del archivo las variables y campos de configuración
    (JsonSerializerSettings con TypeNameHandling inseguro) usados por DeserializeObject.
  - Cada candidato lleva "confianza": alta (un argumento viene de un parámetro del
    método o de Request), media (no se pudo determinar el origen). Las operaciones de
    archivo cuyos argumentos son todos constantes o rutas internas
    (AppContext.BaseDirectory, ContentRootPath, Assembly..., literales) se descartan.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

IGNORAR_DIRS = {"bin", "obj", ".git", "node_modules", "esperado"}

# ---------------------------------------------------------------- lectura de C#


def archivos_cs(ruta: Path) -> list[Path]:
    if ruta.is_file():
        return [ruta] if ruta.suffix == ".cs" else []
    salida = []
    for raiz, dirs, nombres in os.walk(ruta):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR_DIRS)
        salida += [Path(raiz) / n for n in sorted(nombres) if n.endswith(".cs")]
    return salida


def _fin_cadena(texto: str, i: int) -> int:
    """Devuelve el índice justo después de la cadena o carácter que empieza en i."""
    n = len(texto)
    # Prefijos: $"..", @"..", $@"..", @$"..
    j = i
    verbatim = False
    while j < n and texto[j] in "$@":
        verbatim = verbatim or texto[j] == "@"
        j += 1
    comilla = texto[j]
    j += 1
    while j < n:
        c = texto[j]
        if verbatim and c == '"':
            if j + 1 < n and texto[j + 1] == '"':
                j += 2
                continue
            return j + 1
        if not verbatim and c == "\\":
            j += 2
            continue
        if c == comilla:
            return j + 1
        if c == "\n" and not verbatim:
            return j  # cadena sin cerrar: no se arrastra a otras líneas
        j += 1
    return n


def _es_inicio_cadena(texto: str, i: int) -> bool:
    c = texto[i]
    if c == '"':
        return True
    if c == "'":
        # Literal de carácter: 'a', '\n', '\''
        return bool(re.match(r"'(\\.|[^'\\\n])'", texto[i:i + 4]))
    if c in "$@":
        m = re.match(r"[$@]{1,2}\"", texto[i:i + 3])
        return bool(m) and (i == 0 or not (texto[i - 1].isalnum() or texto[i - 1] == "_"))
    return False


def sin_comentarios(texto: str) -> str:
    """Reemplaza comentarios por espacios (conserva saltos de línea y posiciones) sin
    confundir '//' o '/*' dentro de cadenas."""
    salida, i, n = list(texto), 0, len(texto)
    while i < n:
        if texto.startswith("//", i):
            fin = texto.find("\n", i)
            fin = n if fin < 0 else fin
            for k in range(i, fin):
                salida[k] = " "
            i = fin
        elif texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            fin = n if fin < 0 else fin + 2
            for k in range(i, fin):
                if salida[k] != "\n":
                    salida[k] = " "
            i = fin
        elif _es_inicio_cadena(texto, i):
            i = _fin_cadena(texto, i)
        else:
            i += 1
    return "".join(salida)


def lineas_sin_comentarios(texto: str) -> list[str]:
    """Líneas con los comentarios vaciados (mantiene la numeración)."""
    return sin_comentarios(texto).split("\n")


# Un '{' es de inicializador (no abre bloque) si sigue a "new ...", "=", ",", "(", "[",
# "{" o "return": new X { A = 1 }, var a = { 1, 2 }, return new { ... }.
ES_INICIALIZADOR = re.compile(r"(\bnew\b[^;{}]*|(?<![=!<>])=|[,(\[{]|\breturn)\s*$")


class Sentencia:
    """Una sentencia de C# con el texto normalizado (espacios colapsados) y el mapa de
    cada carácter a su línea original."""

    def __init__(self, partes: list[tuple[str, int]]):
        texto, lineas, espacio = [], [], False
        for c, linea in partes:
            if c.isspace():
                if texto and not espacio:
                    texto.append(" ")
                    lineas.append(linea)
                espacio = True
                continue
            espacio = False
            texto.append(c)
            lineas.append(linea)
        while texto and texto[-1] == " ":
            texto.pop()
            lineas.pop()
        self.texto = "".join(texto)
        self._lineas = lineas
        self.linea = lineas[0] if lineas else 0

    def linea_de(self, pos: int) -> int:
        return self._lineas[min(pos, len(self._lineas) - 1)] if self._lineas else 0


def sentencias(texto: str) -> list[Sentencia]:
    """Divide el código (sin comentarios) en sentencias: hasta ';' o '{' de bloque.
    Los '{' de inicializadores (new X { ... }, = { ... }) no cortan la sentencia."""
    limpio = sin_comentarios(texto)
    # Línea (1-based) de cada posición.
    saltos = [i for i, c in enumerate(limpio) if c == "\n"]

    def linea(pos: int) -> int:
        return bisect.bisect_left(saltos, pos) + 1

    resultado: list[Sentencia] = []
    actual: list[tuple[str, int]] = []
    parentesis, inicializadores = 0, []
    i, n = 0, len(limpio)

    def emitir():
        nonlocal actual
        s = Sentencia(actual)
        if s.texto:
            resultado.append(s)
        actual = []

    while i < n:
        c = limpio[i]
        if _es_inicio_cadena(limpio, i):
            fin = _fin_cadena(limpio, i)
            actual += [(ch, linea(i + k)) for k, ch in enumerate(limpio[i:fin])]
            i = fin
            continue
        if c in "([":
            parentesis += 1
        elif c in ")]":
            parentesis = max(0, parentesis - 1)
        if c == "{":
            previo = "".join(ch for ch, _ in actual).rstrip()
            es_bloque = parentesis == 0 and not inicializadores and not ES_INICIALIZADOR.search(previo)
            if es_bloque:
                emitir()
            else:
                inicializadores.append(parentesis)
                actual.append((c, linea(i)))
            i += 1
            continue
        if c == "}":
            if inicializadores:
                inicializadores.pop()
                actual.append((c, linea(i)))
            else:
                emitir()
            i += 1
            continue
        if c == ";" and parentesis == 0 and not inicializadores:
            actual.append((c, linea(i)))
            emitir()
            i += 1
            continue
        actual.append((c, linea(i)))
        i += 1
    emitir()
    return resultado


def relativa(p: Path, base: Path) -> str:
    try:
        return p.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def documento(paso: str, ruta: Path, candidatos: list[dict]) -> dict:
    return {
        "paso": paso,
        "ruta": ruta.as_posix(),
        "generado_por": "agente-sast-g7/scripts/metodologia.py (heurístico, sin razonamiento)",
        "total": len(candidatos),
        "candidatos": candidatos,
    }


def leer(f: Path) -> str:
    return f.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- paso 1: inventario

SENALES = [
    # (nombre, peso, regex)
    ("sql", 3, re.compile(r"SqlCommand|\b(SELECT|INSERT|UPDATE|DELETE)\b\s", re.I)),
    ("comando-sistema", 4, re.compile(r"Process\.Start")),
    ("archivos", 3, re.compile(r"\bFile\.\w+\(|Path\.Combine|IFormFile")),
    ("deserializacion", 4, re.compile(r"BinaryFormatter|\.Deserialize\(|TypeNameHandling")),
    ("red-saliente", 3, re.compile(r"new HttpClient|CreateClient\(|\.(Get|Post|Put|Send)Async\(")),
    ("autenticacion", 3, re.compile(r"Cookies|Redirect\(|SignIn\w*\(|\.Clave\b|\.Password\b|ClaimsPrincipal")),
    ("dinero", 2, re.compile(r"transferencia|\bmonto\b|\bsaldo\b|\bpago\b", re.I)),
]
ENDPOINT = re.compile(r"\[Http(Get|Post|Put|Delete|Patch)\b")


def inventario(ruta: Path) -> dict:
    candidatos = []
    for f in archivos_cs(ruta):
        texto = sin_comentarios(leer(f))
        senales, puntaje = [], 0
        for nombre, peso, rx in SENALES:
            if rx.search(texto):
                senales.append(nombre)
                puntaje += peso
        endpoints = len(ENDPOINT.findall(texto))
        if endpoints:
            senales.append(f"endpoints:{endpoints}")
            puntaje += 2 * min(endpoints, 3)
            if "[Authorize" not in texto:
                senales.append("controlador-sin-authorize")
                puntaje += 3
        nivel = "Alto" if puntaje >= 7 else "Medio" if puntaje >= 4 else "Bajo"
        candidatos.append({
            "archivo": relativa(f, ruta),
            "puntaje": puntaje,
            "nivel": nivel,
            "senales": senales,
        })
    candidatos.sort(key=lambda c: (-c["puntaje"], c["archivo"]))
    for i, c in enumerate(candidatos, 1):
        c["posicion"] = i
    return documento("inventario", ruta, candidatos)


# ---------------------------------------------------------------- paso 2: entradas

TIPOS_SIMPLES = {"string", "int", "long", "decimal", "double", "float", "bool", "Guid",
                 "DateTime", "string?", "int?", "long?", "decimal?", "bool?", "Guid?"}
ATRIBUTO_FUENTE = {
    "FromQuery": "query", "FromRoute": "ruta", "FromBody": "cuerpo",
    "FromHeader": "cabecera", "FromForm": "formulario",
}
RUTA_ATTR = re.compile(r'\[Http\w+\(\s*"([^"]*)"')
# Parámetro con cero o más atributos: [FromQuery][DefaultValue(1)] int page = 1
PARAM = re.compile(r"^\s*((?:\[[^\[\]]*\]\s*)*)([\w<>?\[\],.]+)\s+(\w+)\s*(?:=.*)?$")
ATRIBUTO = re.compile(r"\[\s*(?:\w+\s*\.\s*)*(\w+?)(?:Attribute)?\s*[\](,]")
ACCESO_REQUEST = re.compile(r"Request\s*\.\s*(Query|Headers|Cookies|Form)\s*\[\s*\"([^\"]+)\"")
FUENTE_REQUEST = {"Query": "query", "Headers": "cabecera", "Cookies": "cookie", "Form": "formulario"}
# Firma de método (sentencia que abre bloque): modificadores, tipo, nombre y parámetros.
FIRMA = re.compile(
    r"\b(?:public|private|protected|internal)\b(?:\s+(?:static|async|virtual|override|sealed|new|extern|unsafe))*"
    r"\s+[\w<>\[\],.?]+(?:\s*<[^>]*>)?\s+(\w+)\s*(?:<[^>]*>)?\s*\(")


def _partir_parametros(firma: str) -> list[str]:
    partes, nivel, actual = [], 0, []
    for ch in firma:
        if ch in "<([":
            nivel += 1
        elif ch in ">)]":
            nivel -= 1
        if ch == "," and nivel == 0:
            partes.append("".join(actual))
            actual = []
        else:
            actual.append(ch)
    if "".join(actual).strip():
        partes.append("".join(actual))
    return [p.strip() for p in partes]


def _cierre(texto: str) -> int:
    nivel = 1
    for i, ch in enumerate(texto):
        if ch == "(":
            nivel += 1
        elif ch == ")":
            nivel -= 1
            if nivel == 0:
                return i
    return len(texto)


def _parametros(sentencia: str) -> tuple[str | None, list[tuple[str | None, str, str]]]:
    """(nombre_metodo, [(atributo, tipo, nombre)]) si la sentencia es una firma de método."""
    m = FIRMA.search(sentencia)
    if not m or re.search(r"\b(class|record|struct|interface)\b", sentencia[:m.start(1)]):
        return None, []
    dentro = sentencia[m.end():]
    dentro = dentro[: _cierre(dentro)]
    params = []
    for p in _partir_parametros(dentro):
        mp = PARAM.match(p)
        if mp:
            atributos = [a for a in ATRIBUTO.findall(mp.group(1))]
            fuente = next((a for a in atributos if a in ATRIBUTO_FUENTE), atributos[0] if atributos else None)
            params.append((fuente, mp.group(2), mp.group(3)))
    return m.group(1), params


def entradas(ruta: Path) -> dict:
    candidatos = []
    for f in archivos_cs(ruta):
        plantilla, metodo_actual, archivos_formulario = None, None, set()
        for s in sentencias(leer(f)):
            texto = s.texto
            if ENDPOINT.search(texto):
                m_ruta = RUTA_ATTR.search(texto)
                plantilla = m_ruta.group(1) if m_ruta else ""
            nombre_metodo, params = _parametros(texto)
            if nombre_metodo:
                metodo_actual, archivos_formulario = nombre_metodo, set()
            if nombre_metodo and plantilla is not None:
                linea_firma = s.linea_de(FIRMA.search(texto).start())
                for atributo, tipo, nombre in params:
                    if tipo == "CancellationToken":
                        continue
                    if atributo in ATRIBUTO_FUENTE:
                        fuente = ATRIBUTO_FUENTE[atributo]
                    elif tipo.rstrip("?") in TIPOS_SIMPLES or tipo in TIPOS_SIMPLES:
                        fuente = ("ruta" if re.search(r"\{" + re.escape(nombre) + r"(:[^}]*)?\??\}", plantilla or "")
                                  else "query")
                    else:
                        fuente = "cuerpo"
                    if tipo.startswith("IFormFile"):
                        fuente = "archivo"
                        archivos_formulario.add(nombre)
                    candidatos.append({
                        "archivo": relativa(f, ruta), "linea": linea_firma, "metodo": metodo_actual,
                        "parametro": nombre, "tipo_dato": tipo, "fuente": fuente,
                        "codigo": _recorte(texto[FIRMA.search(texto).start():]),
                    })
                plantilla = None
                continue
            for m in ACCESO_REQUEST.finditer(texto):
                candidatos.append({
                    "archivo": relativa(f, ruta), "linea": s.linea_de(m.start()), "metodo": metodo_actual,
                    "parametro": m.group(2), "tipo_dato": "string",
                    "fuente": FUENTE_REQUEST[m.group(1)], "codigo": _recorte(texto),
                })
            # El nombre de un archivo subido también lo controla el cliente.
            for nombre in archivos_formulario:
                m = re.search(r"\b" + re.escape(nombre) + r"\s*\.\s*FileName\b", texto)
                if m:
                    candidatos.append({
                        "archivo": relativa(f, ruta), "linea": s.linea_de(m.start()),
                        "metodo": metodo_actual, "parametro": f"{nombre}.FileName",
                        "tipo_dato": "string", "fuente": "archivo", "codigo": _recorte(texto),
                    })
    return documento("entradas", ruta,
                     [{"id": f"E-{n:03d}", **c} for n, c in enumerate(candidatos, 1)])


def _recorte(texto: str, maximo: int = 240) -> str:
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


# ---------------------------------------------------------------- paso 3: operaciones

SQL_LITERAL = r'"[^"]*\b(?:select|insert|update|delete)\b[^"]*"'
OPERACIONES = [
    # (categoria, cwe, regex sobre la sentencia normalizada)
    ("sql-dinamico", "CWE-89", re.compile(
        SQL_LITERAL + r"\s*\+|\+\s*" + SQL_LITERAL + r'|\$@?"[^"]*\b(?:select|insert|update|delete)\b[^"]*\{'
        r'|string\.(?:Format|Concat)\(\s*' + SQL_LITERAL, re.I)),
    ("comando-sistema", "CWE-78", re.compile(r"Process\s*\.\s*Start\s*\(|new\s+ProcessStartInfo\s*[({]")),
    ("ruta-archivo", "CWE-22", re.compile(
        r"\b(?:File|Directory)\s*\.\s*(WriteAll\w+|ReadAll\w+|Open\w*|Delete|Create\w*|AppendAll\w+|Copy|Move)\s*\("
        r"|\bPath\s*\.\s*Combine\s*\(|new\s+FileStream\s*\(|\bPhysicalFile\s*\(")),
    ("deserializacion", "CWE-502", re.compile(
        r"new\s+(BinaryFormatter|NetDataContractSerializer|SoapFormatter|LosFormatter|ObjectStateFormatter)\s*\(")),
    ("peticion-saliente", "CWE-918", re.compile(
        r"\.\s*(GetAsync|PostAsync|PutAsync|PatchAsync|SendAsync|GetStringAsync|GetByteArrayAsync|GetStreamAsync|DeleteAsync)\s*\(\s*[A-Za-z_$]")),
    ("redireccion", "CWE-601", re.compile(r"\bRedirect(?:Permanent)?\s*\(\s*(?!\")")),
    ("log-sensible", "CWE-532", re.compile(
        r"(\.Log(Information|Warning|Error|Debug|Trace|Critical)?|Console\s*\.\s*Write\w*)\s*\(.*\b(clave|password|passwd|token|tarjeta|cvv|pin)\b",
        re.I)),
]
NOMBRES_ARGUMENTO = {"ruta-archivo", "comando-sistema", "peticion-saliente", "redireccion", "sql-dinamico"}

INSEGURO_TNH = re.compile(r"TypeNameHandling\s*=\s*TypeNameHandling\s*\.\s*(All|Auto|Objects|Arrays)\b")
DESERIALIZE_OBJECT = re.compile(r"JsonConvert\s*\.\s*DeserializeObject\s*(?:<[^>]*>)?\s*\(")
FORMATTER_DESERIALIZE = re.compile(r"\b(\w+)\s*\.\s*Deserialize\s*\(")

# Orígenes internos: no los controla el cliente.
RUTAS_INTERNAS = re.compile(
    r"^(AppContext\.BaseDirectory|AppDomain\.CurrentDomain\.\w+|Assembly\b.*|typeof\b.*|nameof\b.*"
    r"|Environment\.(GetFolderPath|CurrentDirectory|SpecialFolder)\b.*|Directory\.GetCurrentDirectory"
    r"|Path\.(GetTempPath|GetTempFileName|DirectorySeparatorChar)\b.*"
    r"|\w+\.(ContentRootPath|WebRootPath|BaseDirectory|ApplicationBasePath)|string\.Empty|Guid\.NewGuid.*"
    r"|DateTime\.\w+.*|true|false|null|default)$")


def _quitar_cadenas(expr: str) -> tuple[str, list[str]]:
    """Quita los literales; devuelve el resto y las expresiones de los huecos {..} de
    las cadenas interpoladas."""
    resto, huecos, i = [], [], 0
    while i < len(expr):
        if _es_inicio_cadena(expr, i):
            fin = _fin_cadena(expr, i)
            literal = expr[i:fin]
            if literal.lstrip("@").startswith("$"):
                huecos += [h.split(":")[0] for h in re.findall(r"(?<!\{)\{([^{}]+)\}", literal)]
            resto.append(" ")
            i = fin
        else:
            resto.append(expr[i])
            i += 1
    return "".join(resto), huecos


def _identificadores(expr: str) -> list[str]:
    """Cadenas de acceso a miembros (a.b.c). Los argumentos de las llamadas se analizan
    aparte, así Path.Combine(Carpeta, nombre) devuelve Path.Combine, Carpeta y nombre."""
    internos, sin_llamadas = [], expr
    for _ in range(8):
        internos += re.findall(r"\(([^()]*)\)", sin_llamadas)
        nuevo = re.sub(r"\([^()]*\)", "", sin_llamadas)
        if nuevo == sin_llamadas:
            break
        sin_llamadas = nuevo
    claves = {"new", "var", "await", "return", "this", "base", "is", "as", "out", "ref", "in", "string",
              "int", "long", "object", "decimal", "bool", "byte", "char", "double", "float"}
    resultado = []
    for fragmento in [sin_llamadas] + [i for i in internos if "(" not in i]:
        for c in re.findall(r"[A-Za-z_]\w*(?:\s*\??\.\s*[A-Za-z_]\w*)*", fragmento):
            c = re.sub(r"\s+|\?", "", c)
            if c.split(".")[0] not in claves:
                resultado.append(c)
    return resultado


class Contexto:
    """Lo que se sabe del archivo y del método actual para clasificar un argumento."""

    def __init__(self, constantes: set[str]):
        self.constantes = constantes
        self.parametros: set[str] = set()
        self.locales: dict[str, str] = {}

    def origen(self, expr: str, profundidad: int = 0) -> str:
        """'usuario' si depende de un parámetro o de Request; 'interno' si solo usa
        literales, constantes o rutas internas; 'desconocido' en otro caso."""
        if profundidad > 4:
            return "desconocido"
        resto, huecos = _quitar_cadenas(expr)
        partes = _identificadores(resto) + [i for h in huecos for i in _identificadores(_quitar_cadenas(h)[0])]
        resultado = "interno"
        for ident in partes:
            raiz = ident.split(".")[0]
            if RUTAS_INTERNAS.match(ident):
                continue  # p. ej. env.ContentRootPath aunque env sea un parámetro
            if raiz == "Request" or raiz in self.parametros:
                return "usuario"
            if raiz in self.locales:
                sub = self.origen(self.locales[raiz], profundidad + 1)
                if sub == "usuario":
                    return "usuario"
                if sub == "desconocido":
                    resultado = "desconocido"
                continue
            if raiz in self.constantes or RUTAS_INTERNAS.match(ident) or re.fullmatch(r"\d+", raiz):
                continue
            resultado = "desconocido"
        return resultado


def _argumentos(texto: str, apertura: int) -> list[str]:
    """Argumentos de la llamada cuyo '(' está en la posición apertura."""
    dentro = texto[apertura + 1:]
    return _partir_parametros(dentro[: _cierre(dentro)])


def _constantes(sents: list[Sentencia]) -> set[str]:
    nombres = set()
    for s in sents:
        m = re.search(r"\b(const|static\s+readonly|readonly\s+static)\s+[\w<>\[\]?.]+\s+(\w+)\s*=", s.texto)
        if m:
            nombres.add(m.group(2))
    return nombres


def _ajustes_inseguros(sents: list[Sentencia]) -> dict[str, int]:
    """Variables/campos/propiedades de configuración con TypeNameHandling inseguro → línea."""
    inseguros = {}
    for s in sents:
        m = INSEGURO_TNH.search(s.texto)
        if not m:
            continue
        linea = s.linea_de(m.start())
        # var x = new JsonSerializerSettings { TypeNameHandling = ... }   o   campo/propiedad
        decl = re.search(r"(\w+)\s*=\s*new\s+JsonSerializerSettings\b", s.texto)
        if decl:
            inseguros[decl.group(1)] = linea
        # x.TypeNameHandling = TypeNameHandling.All
        asign = re.search(r"(\w+)\s*\.\s*TypeNameHandling\s*=", s.texto)
        if asign:
            inseguros[asign.group(1)] = linea
        if "DefaultSettings" in s.texto:
            inseguros["<DefaultSettings>"] = linea
        if not (decl or asign or "DefaultSettings" in s.texto):
            inseguros[f"<linea {linea}>"] = linea
    return inseguros


def _ajustes_declarados(sents: list[Sentencia]) -> set[str]:
    """Nombres de variables/campos JsonSerializerSettings declarados en el archivo."""
    nombres = set()
    for s in sents:
        nombres.update(re.findall(r"(\w+)\s*=\s*new\s+JsonSerializerSettings\b", s.texto))
        nombres.update(re.findall(r"JsonSerializerSettings\??\s+(\w+)\s*[=;]", s.texto))
    return nombres


def operaciones(ruta: Path) -> dict:
    candidatos = []
    for f in archivos_cs(ruta):
        sents = sentencias(leer(f))
        ctx = Contexto(_constantes(sents))
        ajustes = _ajustes_inseguros(sents)
        declarados = _ajustes_declarados(sents)
        usados: set[str] = set()
        metodo = None
        propios: list[dict] = []

        def agregar(sent, pos, categoria, cwe, confianza, detalle=""):
            c = {
                "archivo": relativa(f, ruta), "linea": sent.linea_de(pos), "categoria": categoria,
                "cwe": cwe, "codigo": _recorte(sent.texto), "confianza": confianza,
            }
            if metodo:
                c["metodo"] = metodo
            if detalle:
                c["detalle"] = detalle
            propios.append(c)

        for s in sents:
            texto = s.texto
            nombre_metodo, params = _parametros(texto)
            if nombre_metodo:
                metodo = nombre_metodo
                ctx.parametros = {p[2] for p in params}
                ctx.locales = {}
                flecha = texto.find("=>", FIRMA.search(texto).end())
                if flecha < 0:
                    continue  # firma de un método con bloque: el cuerpo viene en otras sentencias
            # Variables locales: var x = expr;  Tipo x = expr;
            m_local = re.match(r"^(?:using\s+)?(?:var|[\w<>\[\]?.]+)\s+(\w+)\s*=\s*(.+?);?$", texto)
            if m_local and m_local.group(1) not in ("new",):
                ctx.locales[m_local.group(1)] = m_local.group(2)

            for categoria, cwe, rx in OPERACIONES:
                for m in rx.finditer(texto):
                    confianza, detalle = "alta", ""
                    if categoria in NOMBRES_ARGUMENTO:
                        if categoria == "sql-dinamico":
                            origen = ctx.origen(texto)
                        else:
                            apertura = texto.find("(", m.start())
                            args = _argumentos(texto, apertura) if apertura >= 0 else []
                            origenes = [ctx.origen(a) for a in args] or ["desconocido"]
                            origen = ("usuario" if "usuario" in origenes else
                                      "interno" if all(o == "interno" for o in origenes) else "desconocido")
                        if origen == "interno" and categoria == "ruta-archivo":
                            continue  # rutas construidas solo con constantes o rutas internas
                        if origen != "usuario":
                            confianza = "media"
                            detalle = ("argumentos de origen no determinado" if origen == "desconocido"
                                       else "argumentos constantes o internos")
                    agregar(s, m.start(), categoria, cwe, confianza, detalle)
                    break  # una coincidencia por categoría y sentencia

            # Newtonsoft: DeserializeObject con configuración insegura (aunque esté definida aparte).
            m = DESERIALIZE_OBJECT.search(texto)
            if m:
                args = _argumentos(texto, texto.find("(", m.end() - 1))
                origen_ajustes = None
                for a in args[1:]:
                    nombre = re.sub(r"^(this|_?\w+)\.", "", a.strip()) if a.strip().startswith("this.") else a.strip()
                    if nombre in ajustes:
                        origen_ajustes = (nombre, ajustes[nombre])
                    elif INSEGURO_TNH.search(a):
                        origen_ajustes = ("inline", s.linea_de(m.start()))
                if not origen_ajustes and len(args) == 1 and "<DefaultSettings>" in ajustes:
                    origen_ajustes = ("JsonConvert.DefaultSettings", ajustes["<DefaultSettings>"])
                if origen_ajustes:
                    usados.add(origen_ajustes[0])
                    agregar(s, m.start(), "deserializacion", "CWE-502", "alta",
                            f"TypeNameHandling inseguro en '{origen_ajustes[0]}' (línea {origen_ajustes[1]})")
                elif len(args) > 1 and not any(a.strip().removeprefix("this.") in declarados for a in args[1:]):
                    agregar(s, m.start(), "deserializacion", "CWE-502", "media",
                            "configuración de deserialización no resuelta en el archivo")
            # Formatters inseguros guardados en una variable: f.Deserialize(stream)
            m = FORMATTER_DESERIALIZE.search(texto)
            if m and m.group(1) in ctx.locales and re.search(
                    r"BinaryFormatter|NetDataContractSerializer|SoapFormatter|LosFormatter|ObjectStateFormatter",
                    ctx.locales[m.group(1)]):
                agregar(s, m.start(), "deserializacion", "CWE-502", "alta",
                        f"formatter inseguro en '{m.group(1)}'")

        # TypeNameHandling inseguro que no consume ninguna llamada del archivo (p. ej. global de MVC).
        for nombre, linea in ajustes.items():
            if nombre not in usados and not any(
                    c["categoria"] == "deserializacion" and c["linea"] == linea for c in propios):
                propios.append({
                    "archivo": relativa(f, ruta), "linea": linea, "categoria": "deserializacion",
                    "cwe": "CWE-502", "codigo": "TypeNameHandling inseguro", "confianza": "media",
                    "detalle": f"configuración insegura '{nombre}' sin llamada de deserialización en el archivo",
                })
        propios.sort(key=lambda c: c["linea"])
        candidatos += propios
    return documento("operaciones", ruta,
                     [{"id": f"O-{n:03d}", **c} for n, c in enumerate(candidatos, 1)])


# ---------------------------------------------------------------- identidad de la ejecución


def _commit_objetivo(ruta: Path) -> str | None:
    """Commit corto del proyecto objetivo si es un repo git; None si no lo es.

    Es el ancla para distinguir ejecuciones del MISMO proyecto a medida que se corrige:
    cada corrida queda atada al estado exacto del código analizado.
    """
    base = ruta if ruta.is_dir() else ruta.parent
    try:
        r = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def identidad(ruta: Path, proyecto: str | None = None, run_id: str | None = None) -> dict:
    """Metadatos que hacen cada salida autodescriptiva y rastreable.

    - proyecto: slug del proyecto (por defecto, el nombre de la carpeta objetivo).
    - run_id:   identifica la ejecución; por defecto timestamp + commit del objetivo,
                de modo que varias corridas (del mismo o de distintos proyectos) no chocan.
    """
    proy = proyecto or (ruta.name if ruta.name else "proyecto")
    ahora = datetime.now(timezone.utc)
    ts = ahora.strftime("%Y%m%d-%H%M%S")
    commit = _commit_objetivo(ruta)
    rid = run_id or (f"{ts}-{commit}" if commit else ts)
    return {
        "proyecto": proy,
        "run_id": rid,
        "timestamp": ahora.isoformat(timespec="seconds"),
        "commit": commit,
    }


def con_meta(doc: dict, meta: dict) -> dict:
    """Inserta la identidad de proyecto/ejecución al inicio del documento (tras 'ruta')."""
    fusion: dict = {}
    for clave, valor in doc.items():
        fusion[clave] = valor
        if clave == "ruta":
            fusion.update(meta)
    if "proyecto" not in fusion:  # doc sin 'ruta' (defensivo)
        fusion = {**meta, **fusion}
    return fusion


def _registrar_run(raiz: Path, dir_run: Path, meta: dict, docs: dict) -> None:
    """Deja rastro de la corrida: manifiesto, puntero 'latest' e índice acumulado.

    Estructura resultante bajo <raiz>/<proyecto>/:
        <run_id>/candidatos-*.json   una carpeta por ejecución (no se pisan)
        <run_id>/run.json            manifiesto de la corrida
        latest -> <run_id>           puntero a la última ejecución
      y <raiz>/<proyecto>/_indice.json con el historial de corridas.
    """
    dir_proy = dir_run.parent
    pasos_nuevos = {n: {"total": d.get("total", 0), "archivo": f"candidatos-{n}.json"}
                    for n, d in docs.items()}
    # Fusiona con un run.json previo: correr paso a paso con el mismo run_id acumula pasos.
    manifiesto_f = dir_run / "run.json"
    pasos = {}
    try:
        previo = json.loads(manifiesto_f.read_text(encoding="utf-8"))
        if isinstance(previo.get("pasos"), dict):
            pasos.update(previo["pasos"])
    except (OSError, json.JSONDecodeError):
        pass
    pasos.update(pasos_nuevos)
    cualquier_ruta = next((d.get("ruta") for d in docs.values() if d.get("ruta")), None)
    manifiesto = {
        **meta,
        "ruta": cualquier_ruta,
        "generado_por": "agente-sast-g7/scripts/metodologia.py",
        "pasos": pasos,
    }
    manifiesto_f.write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Puntero 'latest' -> último run_id (symlink; copia del run.json si el SO no deja symlinks).
    latest = dir_proy / "latest"
    try:
        if latest.is_symlink() or latest.exists():
            if latest.is_dir() and not latest.is_symlink():
                import shutil
                shutil.rmtree(latest)
            else:
                latest.unlink()
        latest.symlink_to(meta["run_id"], target_is_directory=True)
    except OSError:
        (dir_proy / "latest.json").write_text(
            json.dumps({"run_id": meta["run_id"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")

    # Índice acumulado de corridas del proyecto (append, más reciente al final).
    indice_f = dir_proy / "_indice.json"
    try:
        indice = json.loads(indice_f.read_text(encoding="utf-8"))
        corridas = indice.get("corridas", []) if isinstance(indice, dict) else []
    except (OSError, json.JSONDecodeError):
        corridas = []
    corridas = [c for c in corridas if c.get("run_id") != meta["run_id"]]
    corridas.append({**meta, "pasos": manifiesto["pasos"]})
    indice_f.write_text(
        json.dumps({"proyecto": meta["proyecto"], "corridas": corridas},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f">> run {meta['run_id']} registrado en {dir_proy}", file=sys.stderr)


# ---------------------------------------------------------------- validar corrida

# Paso → (archivo, clave de la lista, obligatorio)
SALIDAS_PASOS = [
    ("ranking-archivos", "ranking.json", "archivos", True),
    ("mapeo-entradas", "entradas.json", "entradas", True),
    ("mapeo-operaciones", "operaciones.json", "operaciones", True),
    ("trazador-flujos", "flujos.json", "flujos", True),
    ("analizador-gaps", "gaps.json", "gaps", False),  # se omite si no hay requisitos
    ("devils-advocate", "validacion.json", "veredictos", True),
    ("priorizador-cwe-owasp", "priorizacion.json", "hallazgos", True),
    ("remediador", "remediacion.json", "recomendaciones", True),
]


def validar_corrida(dir_run: Path) -> tuple[list[str], list[str], list[dict]]:
    """Comprueba en un solo paso los JSON de una corrida: existen, se leen, tienen la lista
    esperada, son del mismo objetivo (ruta/proyecto/run_id) y la trazabilidad de ids
    (validación → priorización → remediación). Devuelve (errores, avisos, resumen)."""
    errores: list[str] = []
    avisos: list[str] = []
    resumen: list[dict] = []
    docs: dict[str, dict] = {}
    for paso, nombre, clave, obligatorio in SALIDAS_PASOS:
        f = dir_run / nombre
        if not f.exists():
            (errores if obligatorio else avisos).append(f"falta {nombre} ({paso})")
            resumen.append({"paso": paso, "archivo": nombre, "estado": "falta", "items": 0})
            continue
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            errores.append(f"{nombre}: JSON ilegible ({e})")
            resumen.append({"paso": paso, "archivo": nombre, "estado": "ilegible", "items": 0})
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get(clave), list):
            errores.append(f"{nombre}: falta la lista '{clave}'")
            resumen.append({"paso": paso, "archivo": nombre, "estado": "sin-lista", "items": 0})
            continue
        docs[nombre] = doc
        resumen.append({"paso": paso, "archivo": nombre, "estado": "ok", "items": len(doc[clave])})

    # Mismo objetivo: cada campo de identidad presente debe coincidir en todos los JSON.
    for campo in ("ruta", "proyecto", "run_id"):
        valores = {n: d[campo] for n, d in docs.items() if d.get(campo)}
        distintos = set(valores.values())
        if len(distintos) > 1:
            errores.append(f"'{campo}' no coincide: " + ", ".join(f"{n}={v}" for n, v in valores.items()))
        elif docs and len(valores) < len(docs) and campo != "ruta":
            sin = sorted(set(docs) - set(valores))
            avisos.append(f"sin '{campo}' en: {', '.join(sin)}")

    # Trazabilidad de ids.
    origen = {x.get("id") for n, clave in (("flujos.json", "flujos"), ("gaps.json", "gaps"))
              if n in docs for x in docs[n][clave]}
    if "validacion.json" in docs:
        vers = docs["validacion.json"]["veredictos"]
        huerfanos = sorted({v.get("id_hallazgo") for v in vers} - origen - {None})
        if origen and huerfanos:
            errores.append(f"validacion.json cita ids que no están en flujos/gaps: {huerfanos}")
        vivos = {v.get("id_hallazgo") for v in vers if v.get("veredicto") == "sobrevive"}
        if "priorizacion.json" in docs:
            prio = {h.get("id_hallazgo") for h in docs["priorizacion.json"]["hallazgos"]}
            if prio - vivos:
                errores.append(f"priorizacion.json incluye ids no sobrevivientes: {sorted(prio - vivos)}")
            if vivos - prio:
                avisos.append(f"sobrevivientes sin priorizar: {sorted(vivos - prio)}")
            if "remediacion.json" in docs:
                rem = {r.get("id_hallazgo") for r in docs["remediacion.json"]["recomendaciones"]}
                if rem - prio:
                    errores.append(f"remediacion.json incluye ids no priorizados: {sorted(rem - prio)}")
                if prio - rem:
                    avisos.append(f"priorizados sin remediación: {sorted(prio - rem)}")

    if "priorizacion.json" in docs:
        e2, a2 = validar_cwe_owasp(docs["priorizacion.json"]["hallazgos"])
        errores += e2
        avisos += a2
    return errores, avisos, resumen


def validar_cwe_owasp(hallazgos: list[dict]) -> tuple[list[str], list[str]]:
    """Contrasta CWE y OWASP de la priorización con la KB (agente-sast-g7/kb/cwe-owasp.json).

    Error: CWE que no existe en el catálogo de MITRE. Aviso: CWE cuyo uso MITRE desaconseja
    o prohíbe, y OWASP distinto del mapeo oficial directo del CWE."""
    import kb  # noqa: PLC0415 (solo hace falta al validar)
    errores: list[str] = []
    avisos: list[str] = []
    if not kb.catalogo():
        return errores, ["KB CWE no disponible: no se contrastan CWE ni OWASP"]
    for h in hallazgos:
        hid = h.get("id_hallazgo")
        cwe = kb.normalizar_cwe(h.get("cwe"))
        if not cwe:
            avisos.append(f"{hid}: sin CWE")
            continue
        entrada = kb.buscar_cwe(cwe)
        if entrada is None:
            errores.append(f"{hid}: {cwe} no existe en el catálogo CWE (kb/cwe-owasp.json)")
            continue
        if entrada.get("uso") in ("Discouraged", "Prohibited"):
            avisos.append(f"{hid}: MITRE marca {cwe} como {entrada['uso']}; usa un CWE más concreto")
        oficial = entrada.get("owasp_2021") or []
        oficial = [oficial] if isinstance(oficial, str) else oficial
        dado = str(h.get("owasp") or "")
        if oficial and dado[:8] not in {o[:8] for o in oficial}:
            avisos.append(f"{hid}: OWASP '{dado}' no coincide con el mapeo oficial de {cwe}: "
                          f"'{' | '.join(oficial)}'")
    return errores, avisos


# ---------------------------------------------------------------- CLI

PASOS = {"inventario": inventario, "entradas": entradas, "operaciones": operaciones}


def escribir(doc: dict, destino: str | None) -> None:
    texto = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if destino:
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        Path(destino).write_text(texto, encoding="utf-8")
        print(f">> {doc['paso']}: {doc['total']} candidatos → {destino}", file=sys.stderr)
    else:
        sys.stdout.write(texto)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nombre in PASOS:
        s = sub.add_parser(nombre)
        s.add_argument("ruta")
        s.add_argument("-o", "--salida")
        s.add_argument("--dir", default="salida/reportes/metodologia")
        s.add_argument("--proyecto", help="slug del proyecto (por defecto, nombre de la carpeta)")
        s.add_argument("--run-id", help="id de ejecución (por defecto, timestamp + commit del objetivo)")
        s.add_argument("--run", action="store_true",
                       help="escribe en <dir>/<proyecto>/<run_id>/candidatos-<paso>.json (comparte --run-id con los demás pasos)")
    s = sub.add_parser("todo")
    s.add_argument("ruta")
    s.add_argument("--dir", default="salida/reportes/metodologia")
    s.add_argument("--proyecto", help="slug del proyecto (por defecto, nombre de la carpeta)")
    s.add_argument("--run-id", help="id de ejecución (por defecto, timestamp + commit del objetivo)")
    s.add_argument("--run", action="store_true",
                   help="escribe en <dir>/<proyecto>/<run_id>/ (sin pisar corridas previas) y actualiza latest/ e índice")
    s = sub.add_parser("validar", help="comprueba en un comando los 8 JSON de una corrida")
    s.add_argument("dir_run", help="carpeta $RUN (o salida/reportes/metodologia/<proyecto>/latest)")
    s.add_argument("--json", action="store_true", help="imprime el resultado como JSON")
    args = ap.parse_args(argv)

    if args.cmd == "validar":
        dir_run = Path(args.dir_run)
        if not dir_run.is_dir():
            print(f"ERROR: no existe {dir_run}", file=sys.stderr)
            return 1
        errores, avisos, resumen = validar_corrida(dir_run)
        if args.json:
            print(json.dumps({"dir": str(dir_run), "ok": not errores, "errores": errores,
                              "avisos": avisos, "pasos": resumen}, ensure_ascii=False, indent=2))
        else:
            for r in resumen:
                print(f"{r['estado']:>9}  {r['items']:>4}  {r['archivo']:<18} {r['paso']}")
            for a in avisos:
                print(f"AVISO: {a}")
            for e in errores:
                print(f"ERROR: {e}")
            print("OK: corrida consistente" if not errores else f"{len(errores)} error(es)")
        return 0 if not errores else 2

    ruta = Path(args.ruta)
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}", file=sys.stderr)
        return 1

    meta = identidad(ruta, getattr(args, "proyecto", None), getattr(args, "run_id", None))

    if args.cmd == "todo":
        base = Path(args.dir)
        if args.run:
            base = base / meta["proyecto"] / meta["run_id"]
        docs = {}
        for nombre, funcion in PASOS.items():
            doc = con_meta(funcion(ruta), meta)
            docs[nombre] = doc
            escribir(doc, str(base / f"candidatos-{nombre}.json"))
        if args.run:
            _registrar_run(Path(args.dir), base, meta, docs)
    else:
        doc = con_meta(PASOS[args.cmd](ruta), meta)
        if getattr(args, "run", False):
            base = Path(args.dir) / meta["proyecto"] / meta["run_id"]
            escribir(doc, str(base / f"candidatos-{args.cmd}.json"))
            _registrar_run(Path(args.dir), base, meta, {args.cmd: doc})
        else:
            escribir(doc, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
