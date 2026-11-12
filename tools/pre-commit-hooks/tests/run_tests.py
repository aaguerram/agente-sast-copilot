#!/usr/bin/env python3
"""Pruebas de los hooks .NET de pre-commit (solo biblioteca estándar).

    docker compose --profile seguridad run --rm pre-commit-hooks-tests

Cada fixture declara lo que espera:
  - comentario «ESPERA <id> [<id>...]» en la línea que debe disparar, y/o
  - archivo hermano «<fixture>.esperado» con líneas «<id> <línea> [<línea>...]»
    (para JSON, que no admite comentarios, o líneas donde un comentario cambiaría el
    resultado).
Los archivos «*negativo*» no deben disparar nada. Se compara el conjunto exacto
(regla, línea): sobra o falta un hallazgo → la prueba falla.
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

import dotnet_buenas_practicas as h  # noqa: E402

FIXTURES = AQUI / "fixtures"

REGLAS_POR_TIPO = {
    ".cs": [
        "dotnet-url-quemada", "dotnet-credencial-quemada", "dotnet-tls-sin-validar",
        "dotnet-cors-inseguro", "dotnet-developer-exception-page",
        "dotnet-deserializacion-insegura", "dotnet-hash-debil", "dotnet-random-inseguro",
        "dotnet-supresion-sin-justificar", "dotnet-swagger-sin-entorno",
        "dotnet-catch-vacio", "dotnet-async-bloqueante",
    ],
    ".json": ["dotnet-secreto-en-config", "dotnet-allowed-hosts-comodin"],
    ".csproj": ["dotnet-paquete-version-flotante"],
}


def esperados(ruta: Path) -> set[tuple[str, int]]:
    exp: set[tuple[str, int]] = set()
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        m = re.search(r"ESPERA\s+([\w\s-]+?)\s*(?:-->|$)", linea)
        if m:
            exp |= {(rid, n) for rid in m.group(1).split()}
    lado = ruta.with_name(ruta.name + ".esperado")
    if lado.exists():
        for linea in lado.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                rid, *nums = linea.split()
                exp |= {(rid, int(x)) for x in nums}
    return exp


def encontrados(ruta: Path, permitidos=()) -> set[tuple[str, int]]:
    res = set()
    for rid in REGLAS_POR_TIPO[ruta.suffix]:
        for hz in h.revisar(h.REGLAS[rid], str(ruta.relative_to(FIXTURES)), ruta.read_text(encoding="utf-8"), list(permitidos)):
            res.add((rid, hz.linea))
    return res


class Fixtures(unittest.TestCase):
    def test_fixtures(self):
        archivos = sorted(p for p in FIXTURES.rglob("*") if p.suffix in REGLAS_POR_TIPO)
        self.assertTrue(archivos, "no hay fixtures")
        for ruta in archivos:
            with self.subTest(fixture=str(ruta.relative_to(FIXTURES))):
                exp = set() if "negativo" in ruta.name else esperados(ruta)
                if "positivo" in ruta.name:
                    self.assertTrue(exp, "un positivo debe declarar lo que espera")
                got = encontrados(ruta)
                self.assertEqual(sorted(got - exp), [], "hallazgos de más (falsos positivos)")
                self.assertEqual(sorted(exp - got), [], "hallazgos que faltan (falsos negativos)")

    def test_cada_regla_tiene_positivo(self):
        cubiertas = {rid for p in FIXTURES.rglob("*positivo*") if p.suffix in REGLAS_POR_TIPO for rid, _ in esperados(p)}
        self.assertEqual(sorted(set(h.REGLAS) - cubiertas), [], "reglas sin caso positivo")

    def test_permitidos_txt(self):
        ruta = FIXTURES / "config" / "appsettings.Production.positivo.json"
        sin = encontrados(ruta, [])
        con = encontrados(ruta, [("dotnet-secreto-en-config", "config/appsettings.Production.*.json")])
        self.assertTrue(any(r == "dotnet-secreto-en-config" for r, _ in sin))
        self.assertFalse(any(r == "dotnet-secreto-en-config" for r, _ in con))


class CodigoDeSalida(unittest.TestCase):
    def correr(self, *args) -> tuple[int, str]:
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = h.main(list(args))
        return codigo, salida.getvalue()

    def test_bloquea(self):
        codigo, out = self.correr("--regla", "dotnet-hash-debil", str(FIXTURES / "cs" / "positivo.cs"))
        self.assertEqual(codigo, 1)
        self.assertIn("pre-commit:allow dotnet-hash-debil", out)

    def test_avisa_no_bloquea(self):
        codigo, out = self.correr("--regla", "dotnet-catch-vacio", str(FIXTURES / "cs" / "positivo.cs"))
        self.assertEqual(codigo, 0)
        self.assertIn("AVISO", out)

    def test_negativo_limpio(self):
        args = []
        for rid in REGLAS_POR_TIPO[".cs"]:
            args += ["--regla", rid]
        codigo, out = self.correr(*args, str(FIXTURES / "cs" / "negativo.cs"))
        self.assertEqual((codigo, out), (0, ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
