#!/usr/bin/env python3
"""Hooks de pre-commit con buenas prácticas de seguridad para .NET.

Complementan a SonarQube Community, Semgrep y gitleaks: revisan antes del commit lo que
esas herramientas no cubren, no bloquean o no ven (archivos de configuración, .csproj,
convenciones del equipo). Solo usa la biblioteca estándar.

    python dotnet_buenas_practicas.py --regla dotnet-url-quemada archivo.cs ...
    python dotnet_buenas_practicas.py --listar

Cada regla es "bloquea" (código de salida 1 si hay hallazgos) o "avisa" (muestra los
hallazgos y sale con 0). Para aceptar un hallazgo concreto:

    - En .cs / .csproj: un comentario en la misma línea o en la anterior
          // pre-commit:allow <id-regla> <motivo>
    - En cualquier archivo (por ejemplo JSON, que no admite comentarios): una línea en
      tools/pre-commit-hooks/permitidos.txt
          <id-regla> <ruta o patrón glob> <motivo>
"""

from __future__ import annotations

import argparse
import bisect
import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

AQUI = Path(__file__).resolve().parent
PERMITIDOS = AQUI / "permitidos.txt"

MARCA_PERMISO = re.compile(r"pre-commit:allow\s+([\w-]+)\s+\S")


# --------------------------------------------------------------------------- modelo
@dataclass
class Hallazgo:
    regla: str
    ruta: str
    linea: int
    detalle: str = ""


@dataclass
class Regla:
    id: str
    nombre: str
    severidad: str  # "bloquea" | "avisa"
    mensaje: str
    referencia: str
    revisar: Callable[["Fuente"], Iterable[tuple[int, str]]]


@dataclass
class Fuente:
    ruta: str
    texto: str
    _cs: tuple[str, list[tuple[int, int, str]]] | None = field(default=None, repr=False)
    _inicios: list[int] | None = field(default=None, repr=False)

    @property
    def lineas(self) -> list[str]:
        return self.texto.splitlines()

    def linea_de(self, pos: int) -> int:
        if self._inicios is None:
            self._inicios = [0] + [m.end() for m in re.finditer(r"\n", self.texto)]
        return bisect.bisect_right(self._inicios, pos)

    @property
    def cs(self) -> tuple[str, list[tuple[int, int, str]]]:
        """(código sin comentarios, [(línea, posición, contenido de cada literal)])."""
        if self._cs is None:
            self._cs = _lexer_cs(self.texto)
        return self._cs

    @property
    def es_prueba(self) -> bool:
        return bool(re.search(r"(^|[/\\.])Tests?([/\\.]|$)|[/\\]tests?[/\\]", self.ruta))


# --------------------------------------------------------------------------- lexer C#
def _lexer_cs(texto: str) -> tuple[str, list[tuple[int, int, str]]]:
    """Reemplaza los comentarios por espacios (conservando saltos de línea y posiciones)
    y devuelve los literales de cadena con su línea. Cubre "...", @"...", $"...",
    raw strings \"\"\"...\"\"\" y literales de carácter."""
    out = list(texto)
    literales: list[tuple[int, int, str]] = []
    n = len(texto)
    linea = 1
    i = 0

    def borrar(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = texto[i]
        if c == "\n":
            linea += 1
            i += 1
            continue
        if texto.startswith("//", i):
            fin = texto.find("\n", i)
            fin = n if fin == -1 else fin
            borrar(i, fin)
            i = fin
            continue
        if texto.startswith("/*", i):
            fin = texto.find("*/", i + 2)
            fin = n if fin == -1 else fin + 2
            borrar(i, fin)
            linea += texto.count("\n", i, fin)
            i = fin
            continue
        # prefijos $ y @ de cadenas
        j = i
        verbatim = False
        while j < n and texto[j] in "$@" and j - i < 4:
            verbatim = verbatim or texto[j] == "@"
            j += 1
        if j < n and texto[j] == '"' and (j > i or c == '"'):
            inicio_linea = linea
            # raw string literal: 3 o más comillas
            k = j
            while k < n and texto[k] == '"':
                k += 1
            comillas = k - j
            if comillas >= 3:
                cierre = texto.find('"' * comillas, k)
                cierre = n if cierre == -1 else cierre
                contenido = texto[k:cierre]
                fin = min(n, cierre + comillas)
            elif verbatim:
                k = j + 1
                partes = []
                while k < n:
                    if texto[k] == '"':
                        if k + 1 < n and texto[k + 1] == '"':
                            partes.append('"')
                            k += 2
                            continue
                        break
                    partes.append(texto[k])
                    k += 1
                contenido = "".join(partes)
                fin = min(n, k + 1)
            else:
                k = j + 1
                while k < n and texto[k] not in '"\n':
                    k += 2 if texto[k] == "\\" else 1
                contenido = texto[j + 1 : min(k, n)]
                fin = min(n, k + 1)
            literales.append((inicio_linea, j, contenido))
            linea += texto.count("\n", i, fin)
            i = fin
            continue
        if c == "'":
            k = i + 1
            if k < n and texto[k] == "\\":
                k += 2
            else:
                k += 1
            while k < n and texto[k] not in "'\n" and k - i < 12:
                k += 1
            i = k + 1 if k < n and texto[k] == "'" else i + 1
            continue
        i += 1
    return "".join(out), literales


# --------------------------------------------------------------------------- utilidades
MARCADOR_DE_POSICION = re.compile(
    r"""^\s*$|^\$\{.*\}$|^\#\{.*\}\#?$|^<.*>$|^__\w+__$|^\{\{.*\}\}$|^%\w+%$|^\$\(.*\)$
    |^(?i:changeme|change[-_]me|cambiar|cambiame|completar|placeholder|secret|password
        |dummy|fake|n/?a|none|null|todo|xx+|\*+|\.+)$""",
    re.X,
)

CLAVE_SECRETA = re.compile(
    r"(?i)(password|passwd|pwd|secret|api[-_]?key|token|access[-_]?key|private[-_]?key"
    r"|client[-_]?secret|credential|sas[-_]?key|signing[-_]?key)"
)

CONEXION_CON_CLAVE = re.compile(
    r"(?i)\b(password|pwd|accountkey|sharedaccesskey)\s*=\s*([^;\"'\s]+)"
)


def _es_marcador(valor: str) -> bool:
    return bool(MARCADOR_DE_POSICION.match(valor.strip()))


def _no_es_secreto(valor: str) -> bool:
    """Valores que no son credenciales aunque la clave lo sugiera (TokenLifetime: "30",
    TokenEndpoint: "https://...", mensajes de validación, rutas)."""
    v = valor.strip()
    return bool(
        _es_marcador(v)
        or re.search(r"\s", v)
        or re.fullmatch(r"-?\d+(\.\d+)?|(?i:true|false)|\d+(:\d{2}){1,2}(\.\d+)?", v)
        or re.match(ESQUEMAS_URL, v, re.I)
        or v.startswith(("/", "~/", "./"))
    )


URL_CON_CLAVE = re.compile(r"://[^/@\s:\"]+:([^/@\s\"]+)@")


def _conexion_con_clave(texto: str) -> bool:
    m = URL_CON_CLAVE.search(texto)
    if m and not _es_marcador(m.group(1)) and not m.group(1).startswith(("{", "$")):
        return True
    for m in CONEXION_CON_CLAVE.finditer(texto):
        if not _es_marcador(m.group(2)) and not m.group(2).startswith("{"):
            return True
    return False


def _tras_si_desarrollo(lineas: list[str], idx: int, ventana: int = 6) -> bool:
    """True si alguna de las líneas previas abre un `if (...IsDevelopment())` (sin `!`)."""
    for k in range(max(0, idx - ventana), idx + 1):
        if re.search(r"(?<!!)\b\w*\.?IsDevelopment\(\)", lineas[k]) and not re.search(
            r"!\s*\w[\w.]*IsDevelopment\(\)", lineas[k]
        ):
            return True
    return False


def _en_lineas(fuente: Fuente, patron: re.Pattern[str], texto: str | None = None):
    texto = fuente.cs[0] if texto is None else texto
    for m in patron.finditer(texto):
        yield fuente.linea_de(m.start()), m.group(0).strip()


# --------------------------------------------------------------------------- reglas .cs
ESQUEMAS_URL = r"(?:https?|ftp|wss?|amqps?|mqtt|sftp|ldaps?|redis|mongodb(?:\+srv)?)://"
URL_LITERAL = re.compile(r"^\s*" + ESQUEMAS_URL + r"([^/\s:?#\"]+)", re.I)
IP_LITERAL = re.compile(r"^\s*(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(:\d+)?\s*$")
HOSTS_NO_RED = re.compile(
    r"(?i)^(www\.w3\.org|schemas\.(xmlsoap\.org|microsoft\.com|openxmlformats\.org"
    r"|android\.com)|json-schema\.org|purl\.org|tempuri\.org|xmlns\.com|ns\.adobe\.com"
    r"|docs\.oasis-open\.org)$"
)
HOSTS_LOCALES = re.compile(r"(?i)^(localhost|127\.\d+\.\d+\.\d+|\[::1\]|0\.0\.0\.0|host\.docker\.internal)$")


def r_url_quemada(f: Fuente):
    for linea, _, valor in f.cs[1]:
        m = URL_LITERAL.match(valor)
        if m:
            host = m.group(1)
            if host.startswith("{") or HOSTS_NO_RED.match(host):
                continue
            if HOSTS_LOCALES.match(host) and f.es_prueba:
                continue
            yield linea, valor.strip()[:100]
            continue
        ip = IP_LITERAL.match(valor)
        if ip:
            octetos = [int(x) for x in ip.groups()[:4]]
            if max(octetos) > 255 or octetos[0] in (0, 127) or octetos == [255] * 4:
                continue
            yield linea, valor.strip()


ASIGNACION_SECRETO = re.compile(
    r"(?i)\b(\w*(?:password|passwd|pwd|secret|apikey|api_key|token|clientsecret|accesskey"
    r"|privatekey|signingkey)\w*)\s*(?:\{[^{}]*\}\s*)?(?:=|:|=>)\s*@?\$?\"([^\"\n]{6,})\""
)


def r_credencial_quemada(f: Fuente):
    codigo, literales = f.cs
    for linea, _, valor in literales:
        if _conexion_con_clave(valor):
            yield linea, "cadena de conexión con contraseña"
    for m in ASIGNACION_SECRETO.finditer(codigo):
        valor = m.group(2)
        if _no_es_secreto(valor):
            continue
        # nombres de claves de configuración o variables de entorno, no valores
        if re.fullmatch(r"[A-Za-z0-9_.-]+(:[A-Za-z0-9_.-]+)+|[A-Z0-9_]+", valor):
            continue
        if _conexion_con_clave(valor):
            continue  # ya reportado arriba
        yield f.linea_de(m.start()), f"{m.group(1)} = \"…\""


TLS_CALLBACK = re.compile(
    r"(ServerCertificateCustomValidationCallback|ServerCertificateValidationCallback"
    r"|RemoteCertificateValidationCallback|CertificateValidationCallback)\s*\+?=\s*"
    r"(?:\([^)]*\)|\w+|delegate\s*(?:\([^)]*\))?)\s*(?:=>)?\s*\{?\s*(?:return\s+)?true\b",
    re.S,
)
TLS_OTROS = re.compile(
    r"\bDangerousAcceptAnyServerCertificateValidator\b"
    r"|\bSslProtocols\.(?:Ssl2|Ssl3|Tls|Tls11)\b"
    r"|\bSecurityProtocolType\.(?:Ssl3|Tls|Tls11)\b"
    r"|CheckCertificateRevocationList\s*=\s*false"
)


def r_tls(f: Fuente):
    yield from _en_lineas(f, TLS_CALLBACK)
    yield from _en_lineas(f, TLS_OTROS)


ORIGEN_ABIERTO = re.compile(
    r"\.AllowAnyOrigin\s*\(\s*\)|\.SetIsOriginAllowed\s*\(\s*\w*\s*=>\s*true\s*\)"
    r"|\.WithOrigins\s*\(\s*\"\*\"\s*\)"
)
CREDENCIALES = re.compile(r"\.AllowCredentials\s*\(\s*\)")


def r_cors(f: Fuente):
    """Origen abierto y AllowCredentials() en la MISMA política (misma sentencia)."""
    codigo = f.cs[0]
    for m in CREDENCIALES.finditer(codigo):
        inicio = codigo.rfind(";", 0, m.start()) + 1
        fin = codigo.find(";", m.end())
        if ORIGEN_ABIERTO.search(codigo[inicio : fin if fin != -1 else len(codigo)]):
            yield f.linea_de(m.start()), "origen abierto + AllowCredentials()"


def _sin_entorno(f: Fuente, patron: re.Pattern[str]):
    lineas = f.cs[0].splitlines()
    for idx, texto in enumerate(lineas):
        if patron.search(texto) and not _tras_si_desarrollo(lineas, idx):
            yield idx + 1, texto.strip()


def r_developer_exception(f: Fuente):
    yield from _sin_entorno(f, re.compile(r"\bUseDeveloperExceptionPage\s*\("))


def r_swagger(f: Fuente):
    yield from _sin_entorno(f, re.compile(r"\b(UseSwagger|UseSwaggerUI|MapOpenApi|MapScalarApiReference)\s*\("))


DESERIALIZACION = re.compile(
    r"\b(BinaryFormatter|NetDataContractSerializer|SoapFormatter|LosFormatter"
    r"|ObjectStateFormatter)\b"
    r"|TypeNameHandling\s*=\s*TypeNameHandling\.(?:All|Auto|Objects|Arrays)\b"
    r"|new\s+JavaScriptSerializer\s*\(\s*new\s+SimpleTypeResolver"
)


def r_deserializacion(f: Fuente):
    yield from _en_lineas(f, DESERIALIZACION)


HASH_DEBIL = re.compile(
    r"\b(?:MD5|SHA1)\s*\.\s*(?:Create|HashData|HashDataAsync)\b"
    r"|new\s+(?:MD5CryptoServiceProvider|SHA1CryptoServiceProvider|SHA1Managed|SHA1Cng"
    r"|MD5Cng|HMACMD5|HMACSHA1|RIPEMD160Managed)\b"
    r"|HashAlgorithmName\.(?:MD5|SHA1)\b"
)


def r_hash_debil(f: Fuente):
    yield from _en_lineas(f, HASH_DEBIL)


RANDOM = re.compile(r"\bnew\s+Random\s*\(|\bRandom\.Shared\b")
CONTEXTO_SENSIBLE = re.compile(
    r"(?i)(token|password|passwd|contrase|secret|salt|otp|nonce|api_?key|pin\b|reset"
    r"|verification|verificacion|session|sesion|csrf)"
)


CABECERA_MIEMBRO = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|static|async|override|virtual|sealed|unsafe)\s+)+[^;=]*\("
)


def r_random(f: Fuente):
    """new Random() / Random.Shared dentro de un miembro cuyo nombre o cuerpo cercano
    habla de tokens, contraseñas, salts, OTP, etc."""
    lineas = f.cs[0].splitlines()
    for idx, texto in enumerate(lineas):
        if not RANDOM.search(texto):
            continue
        inicio = next((k for k in range(idx, -1, -1) if CABECERA_MIEMBRO.match(lineas[k])), max(0, idx - 3))
        fin = next((k for k in range(idx + 1, len(lineas)) if CABECERA_MIEMBRO.match(lineas[k])), len(lineas))
        ventana = "\n".join(lineas[inicio : min(fin, idx + 4)])
        if CONTEXTO_SENSIBLE.search(ventana):
            yield idx + 1, texto.strip()


def r_supresion(f: Fuente):
    lineas = f.texto.splitlines()
    for idx, texto in enumerate(lineas):
        if re.match(r"\s*#pragma\s+warning\s+disable\b", texto) and "//" not in texto:
            yield idx + 1, texto.strip()
    codigo = f.cs[0]
    for m in re.finditer(r"\[\s*(?:assembly\s*:\s*)?(?:[\w.]*\.)?SuppressMessage\s*\(", codigo):
        # el atributo termina en el primer "]" posterior
        fin = codigo.find("]", m.end())
        if "Justification" not in f.texto[m.start() : fin if fin != -1 else None]:
            yield f.linea_de(m.start()), "SuppressMessage sin Justification"


CATCH_VACIO = re.compile(r"\bcatch\s*(?:\([^)]*\))?\s*(?:when\s*\([^)]*\))?\s*\{\s*\}")


def r_catch_vacio(f: Fuente):
    for m in CATCH_VACIO.finditer(f.cs[0]):
        # un comentario dentro del bloque cuenta como justificación
        if re.search(r"//|/\*", f.texto[m.start() : m.end()]):
            continue
        yield f.linea_de(m.start()), re.sub(r"\s+", " ", m.group(0))


ASYNC_BLOQUEANTE = re.compile(
    r"\.Wait\(\s*\)|\.GetAwaiter\(\s*\)\s*\.GetResult\(\s*\)"
    r"|\w+Async\([^;{}]*?\)\s*\.Result\b|\b\w*[Tt]ask\s*\.Result\b"
)


def r_async_bloqueante(f: Fuente):
    yield from _en_lineas(f, ASYNC_BLOQUEANTE)


# --------------------------------------------------------------------------- reglas config
def _linea_de_json(f: Fuente, clave: str, valor: str) -> int:
    patron = re.compile(r'"' + re.escape(clave) + r'"\s*:\s*' + re.escape(json.dumps(valor)))
    m = patron.search(f.texto)
    if m:
        return f.linea_de(m.start())
    pos = f.texto.find(json.dumps(valor)[1:-1])
    return f.linea_de(pos) if pos >= 0 else 1


def _recorrer(nodo, ruta=()):
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            yield from _recorrer(v, ruta + (str(k),))
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo):
            yield from _recorrer(v, ruta + (str(i),))
    else:
        yield ruta, nodo


def _json(f: Fuente):
    try:
        return json.loads(f.texto)
    except ValueError:
        return None  # check-json ya lo reporta


def r_secreto_config(f: Fuente):
    datos = _json(f)
    if datos is None:
        return
    for ruta, valor in _recorrer(datos):
        if not isinstance(valor, str) or not ruta:
            continue
        clave = ruta[-1]
        if _conexion_con_clave(valor):
            yield _linea_de_json(f, clave, valor), ":".join(ruta) + " (contraseña en cadena de conexión)"
        elif CLAVE_SECRETA.search(clave) and not _no_es_secreto(valor):
            yield _linea_de_json(f, clave, valor), ":".join(ruta)


def r_allowed_hosts(f: Fuente):
    datos = _json(f)
    if isinstance(datos, dict) and str(datos.get("AllowedHosts", "")).strip() == "*":
        yield _linea_de_json(f, "AllowedHosts", datos["AllowedHosts"]), '"AllowedHosts": "*"'


PAQUETE_FLOTANTE = re.compile(
    r"<(?:PackageReference|PackageVersion)\b[^>]*\b(?:Version|VersionOverride)\s*=\s*\"([^\"]*\*[^\"]*)\""
    r"|<(?:Version|VersionOverride)>\s*([^<]*\*[^<]*)</",
    re.S,
)


def r_paquete_flotante(f: Fuente):
    for m in PAQUETE_FLOTANTE.finditer(f.texto):
        yield f.linea_de(m.start()), re.sub(r"\s+", " ", m.group(0))[:120]


# --------------------------------------------------------------------------- catálogo
REGLAS: dict[str, Regla] = {
    r.id: r
    for r in [
        Regla("dotnet-url-quemada", "URL, host o IP quemados en el código", "bloquea",
              "Mueve la URL/IP a appsettings.json o a una variable de entorno y léela con "
              "IOptions<T>/IConfiguration (12-Factor III).",
              "OWASP ASVS 5.0 V13.3 · CWE-547 · 12-Factor III · Sonar S1075", r_url_quemada),
        Regla("dotnet-credencial-quemada", "Credencial o cadena de conexión con clave en .cs", "bloquea",
              "Lee el valor de IConfiguration y guárdalo en user-secrets (local) o Key Vault / "
              "variable secreta del pipeline. Si ya se subió, rótalo.",
              "OWASP ASVS 5.0 V13.3.1 · CWE-798 · CWE-259", r_credencial_quemada),
        Regla("dotnet-secreto-en-config", "Secreto con valor real en appsettings (no Development)", "bloquea",
              "Deja el valor vacío o como marcador (${VAR}, #{VAR}#) y aliméntalo por variable "
              "de entorno (Seccion__Clave) o Key Vault.",
              "OWASP ASVS 5.0 V13.3.1 · CWE-798 · CWE-260", r_secreto_config),
        Regla("dotnet-tls-sin-validar", "Validación TLS deshabilitada o protocolo obsoleto", "bloquea",
              "No ignores errores de certificado ni fuerces SSL3/TLS 1.0/1.1; deja que el SO "
              "elija (SslProtocols.None) o usa TLS 1.2+.",
              "OWASP ASVS 5.0 V12.1/V12.3 · CWE-295 · CWE-326", r_tls),
        Regla("dotnet-cors-inseguro", "CORS con cualquier origen y credenciales", "bloquea",
              "Con AllowCredentials() enumera los orígenes permitidos con WithOrigins(...) "
              "leídos de configuración.",
              "OWASP ASVS 5.0 V3.4 · CWE-942", r_cors),
        Regla("dotnet-developer-exception-page", "UseDeveloperExceptionPage sin chequeo de entorno", "bloquea",
              "Envuélvelo en if (app.Environment.IsDevelopment()) y usa UseExceptionHandler en "
              "los demás entornos.",
              "OWASP ASVS 5.0 V16.5 · CWE-209 · CWE-489", r_developer_exception),
        Regla("dotnet-deserializacion-insegura", "Deserialización insegura", "bloquea",
              "BinaryFormatter y similares están obsoletos (SYSLIB0011); usa System.Text.Json. "
              "En Newtonsoft deja TypeNameHandling.None.",
              "OWASP ASVS 5.0 V1.5 · CWE-502 · CA2300-CA2330", r_deserializacion),
        Regla("dotnet-hash-debil", "MD5 / SHA-1", "bloquea",
              "Usa SHA-256+ (o PBKDF2/Argon2 para contraseñas). Si es un checksum no "
              "criptográfico, márcalo con pre-commit:allow y el motivo.",
              "OWASP ASVS 5.0 V11.4 · CWE-327 · CWE-328 · CA5350/CA5351", r_hash_debil),
        Regla("dotnet-random-inseguro", "System.Random para valores sensibles", "bloquea",
              "Para tokens, salts, OTP o claves usa RandomNumberGenerator.GetBytes / GetInt32.",
              "OWASP ASVS 5.0 V11.5 · CWE-338 · CA5394", r_random),
        Regla("dotnet-supresion-sin-justificar", "#pragma warning disable / SuppressMessage sin motivo", "bloquea",
              "Agrega el motivo: '#pragma warning disable CAxxxx // motivo' o "
              "Justification = \"...\".",
              "Microsoft CA/IDE · revisión de excepciones (ASVS V15)", r_supresion),
        Regla("dotnet-paquete-version-flotante", "Paquete NuGet con versión flotante (*)", "bloquea",
              "Fija la versión exacta (o usa Directory.Packages.props) para builds reproducibles "
              "y revisables.",
              "OWASP ASVS 5.0 V15.2 · CWE-1357 · CWE-829 · OWASP Top 10 2025 A03", r_paquete_flotante),
        Regla("dotnet-swagger-sin-entorno", "Swagger/OpenAPI publicado sin chequeo de entorno", "avisa",
              "Exponlo solo en Development (o protégelo con autenticación) si la API no es pública.",
              "OWASP ASVS 5.0 V13.4 · CWE-200 · OWASP API9:2023", r_swagger),
        Regla("dotnet-allowed-hosts-comodin", "AllowedHosts \"*\" fuera de Development", "avisa",
              "Restringe AllowedHosts a los dominios reales por ambiente (filtrado de Host header).",
              "OWASP ASVS 5.0 V13.4 · CWE-644", r_allowed_hosts),
        Regla("dotnet-catch-vacio", "catch vacío", "avisa",
              "Registra la excepción, reláncala o explica con un comentario por qué se ignora.",
              "CWE-390 · CWE-1069 · CA1031", r_catch_vacio),
        Regla("dotnet-async-bloqueante", ".Result / .Wait() / GetResult() sobre tareas", "avisa",
              "Usa await de punta a punta; el bloqueo síncrono provoca deadlocks y agota el "
              "thread pool.",
              "CWE-833 · VSTHRD002 · CA2012", r_async_bloqueante),
    ]
}


# --------------------------------------------------------------------------- ejecución
def _cargar_permitidos() -> list[tuple[str, str]]:
    if not PERMITIDOS.exists():
        return []
    pares = []
    for linea in PERMITIDOS.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = linea.split(maxsplit=2)
        if len(partes) < 3:
            print(f"permitidos.txt: falta el motivo en «{linea}»", file=sys.stderr)
            continue
        pares.append((partes[0], partes[1]))
    return pares


def _suprimido(regla: str, fuente: Fuente, linea: int, permitidos) -> bool:
    ruta = fuente.ruta.replace("\\", "/")
    if any(r == regla and fnmatch.fnmatch(ruta, patron) for r, patron in permitidos):
        return True
    lineas = fuente.lineas
    for k in (linea - 1, linea - 2):
        if 0 <= k < len(lineas):
            m = MARCA_PERMISO.search(lineas[k])
            if m and m.group(1) == regla:
                return True
    return False


def revisar(regla: Regla, ruta: str, texto: str | None = None, permitidos=None) -> list[Hallazgo]:
    if texto is None:
        texto = Path(ruta).read_text(encoding="utf-8-sig", errors="replace")
    fuente = Fuente(ruta, texto)
    permitidos = _cargar_permitidos() if permitidos is None else permitidos
    vistos = set()
    hallazgos = []
    for linea, detalle in regla.revisar(fuente):
        if (linea, detalle) in vistos or _suprimido(regla.id, fuente, linea, permitidos):
            continue
        vistos.add((linea, detalle))
        hallazgos.append(Hallazgo(regla.id, ruta, linea, detalle))
    return sorted(hallazgos, key=lambda h: h.linea)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--regla", action="append", choices=sorted(REGLAS), help="id de regla (repetible)")
    p.add_argument("--listar", action="store_true", help="muestra el catálogo de reglas")
    p.add_argument("archivos", nargs="*")
    a = p.parse_args(argv)

    if a.listar:
        for r in REGLAS.values():
            print(f"{r.id:34} {r.severidad:8} {r.nombre}  [{r.referencia}]")
        return 0
    if not a.regla:
        p.error("indica al menos una --regla")

    permitidos = _cargar_permitidos()
    codigo = 0
    for rid in a.regla:
        regla = REGLAS[rid]
        hallazgos = [h for ruta in a.archivos for h in revisar(regla, ruta, permitidos=permitidos)]
        if not hallazgos:
            continue
        etiqueta = "ERROR" if regla.severidad == "bloquea" else "AVISO"
        for h in hallazgos:
            print(f"{h.ruta}:{h.linea}: {etiqueta} [{regla.id}] {regla.nombre}: {h.detalle}")
        print(f"  → {regla.mensaje}")
        print(f"  → Referencia: {regla.referencia}")
        print(f"  → Si es intencional: comentario 'pre-commit:allow {regla.id} <motivo>' en la línea "
              f"o en la anterior, o una entrada en tools/pre-commit-hooks/permitidos.txt")
        if regla.severidad == "bloquea":
            codigo = 1
    return codigo


if __name__ == "__main__":
    sys.exit(main())
