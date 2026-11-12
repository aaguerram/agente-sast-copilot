#!/usr/bin/env python3
"""Compara los resultados de la metodología SAST con la respuesta de referencia.

    comparar_esperado.py [--actual salida/reportes/metodologia]
                         [--esperado agente-sast-g7/samples/app-vulnerable/esperado]
                         [--estricto]

Muestra, por archivo, cuántos elementos hay en la ejecución actual y en la referencia, y
para los candidatos deterministas (pasos 1-3) qué fallas esperadas de
`fallas-esperadas.json` se encontraron. Los pasos con razonamiento (4-8) varían entre
ejecuciones del modelo: solo se comparan conteos, como orientación.

Sale con 0 salvo con --estricto, que sale con 1 si falta alguna falla esperada en los
candidatos o si algún archivo presente quedó sin elementos. Solo biblioteca estándar.
En el repo:  docker compose --profile agentes run --rm py agente-sast-g7/scripts/comparar_esperado.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# archivo -> clave de la lista principal
ARCHIVOS = [
    ("candidatos-inventario.json", "candidatos", "1 ranking (script)"),
    ("candidatos-entradas.json", "candidatos", "2 entradas (script)"),
    ("candidatos-operaciones.json", "candidatos", "3 operaciones (script)"),
    ("ranking.json", "archivos", "1 ranking"),
    ("entradas.json", "entradas", "2 entradas"),
    ("operaciones.json", "operaciones", "3 operaciones"),
    ("flujos.json", "flujos", "4 flujos"),
    ("gaps.json", "gaps", "5 gaps"),
    ("validacion.json", "veredictos", "6 validación"),
    ("priorizacion.json", "hallazgos", "7 priorización"),
    ("remediacion.json", "recomendaciones", "8 remediación"),
]


def cargar(ruta: Path):
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"AVISO: no se pudo leer {ruta}: {exc}", file=sys.stderr)
        return None


def contar(datos, clave: str):
    if datos is None:
        return None
    if isinstance(datos, list):
        return len(datos)
    valor = datos.get(clave)
    if isinstance(valor, list):
        return len(valor)
    listas = [v for v in datos.values() if isinstance(v, list)]
    return len(listas[0]) if listas else 0


def cobertura(actual_dir: Path, fallas: dict) -> list[tuple[str, int, int, list[str]]]:
    """Fallas esperadas encontradas en los candidatos deterministas (pasos 1-3)."""
    filas = []
    inv = cargar(actual_dir / "candidatos-inventario.json")
    if inv is not None and "ranking" in fallas:
        niveles = {c.get("archivo"): c.get("nivel") for c in inv.get("candidatos", [])}
        alto = fallas["ranking"].get("alto", [])
        faltan = [a for a in alto if niveles.get(a) != "Alto"]
        filas.append(("1 archivos de riesgo Alto", len(alto) - len(faltan), len(alto), faltan))
    ent = cargar(actual_dir / "candidatos-entradas.json")
    if ent is not None and "entradas" in fallas:
        vistos = {(c.get("archivo"), c.get("parametro")) for c in ent.get("candidatos", [])}
        esperadas = fallas["entradas"]
        faltan = [f"{e['archivo']}:{e['parametro']}" for e in esperadas
                  if (e["archivo"], e["parametro"]) not in vistos]
        filas.append(("2 entradas esperadas", len(esperadas) - len(faltan), len(esperadas), faltan))
    ope = cargar(actual_dir / "candidatos-operaciones.json")
    if ope is not None and "operaciones" in fallas:
        vistos = {(c.get("archivo"), c.get("categoria")) for c in ope.get("candidatos", [])}
        esperadas = fallas["operaciones"]
        faltan = [f"{o['archivo']}:{o['categoria']}" for o in esperadas
                  if (o["archivo"], o["categoria"]) not in vistos]
        filas.append(("3 operaciones esperadas", len(esperadas) - len(faltan), len(esperadas), faltan))
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--actual", default="salida/reportes/metodologia")
    ap.add_argument("--esperado", default="agente-sast-g7/samples/app-vulnerable/esperado")
    ap.add_argument("--estricto", action="store_true")
    args = ap.parse_args()
    actual_dir, esperado_dir = Path(args.actual), Path(args.esperado)

    if not actual_dir.is_dir():
        print(f"No existe {actual_dir}: ejecuta antes la metodología (./scripts/agente.sh demo).")
        return 1 if args.estricto else 0

    ruta_actual = None
    problemas = 0
    print(f"Actual:   {actual_dir}\nEsperado: {esperado_dir}\n")
    print(f"| {'Paso':<24} | {'Archivo':<28} | {'Actual':>6} | {'Esperado':>8} |")
    print(f"|{'-' * 26}|{'-' * 30}|{'-' * 8}|{'-' * 10}|")
    for nombre, clave, paso in ARCHIVOS:
        act = cargar(actual_dir / nombre)
        esp = cargar(esperado_dir / nombre)
        if act is None and esp is None:
            continue
        if isinstance(act, dict) and act.get("ruta"):
            ruta_actual = ruta_actual or act["ruta"]
        n_act, n_esp = contar(act, clave), contar(esp, clave)
        txt_act = "—" if n_act is None else str(n_act)
        txt_esp = "—" if n_esp is None else str(n_esp)
        if n_act == 0:
            problemas += 1
            txt_act += " !"
        print(f"| {paso:<24} | {nombre:<28} | {txt_act:>6} | {txt_esp:>8} |")

    fallas = cargar(esperado_dir / "fallas-esperadas.json")
    referencia = cargar(esperado_dir / "ranking.json") or {}
    def normalizar(r: str) -> str:
        return r.replace("\\", "/").strip().rstrip("/").removeprefix("./")

    ruta_ref = normalizar(str(referencia.get("ruta", "")))
    # La ruta puede venir relativa (agente-sast-g7/...) o absoluta (/repo/agente-sast-g7/...).
    misma_ruta = ruta_actual is None or not ruta_ref or \
        normalizar(ruta_actual) == ruta_ref or normalizar(ruta_actual).endswith("/" + ruta_ref)
    if fallas and misma_ruta:
        filas = cobertura(actual_dir, fallas)
        if filas:
            print("\nCobertura de las fallas esperadas (candidatos deterministas):")
            for titulo, ok, total, faltan in filas:
                marca = "OK" if not faltan else "FALTAN"
                print(f"  - {titulo}: {ok}/{total} {marca}")
                for f in faltan:
                    print(f"      · {f}")
                    problemas += 1
    elif not misma_ruta:
        print(f"\nLa ruta analizada ({ruta_actual}) no es la de la referencia: solo se comparan conteos.")

    print("\n'—' = el paso aún no se ejecutó.  '!' = el paso no encontró nada.")
    print("Los pasos 4-8 los razona el modelo: los conteos pueden variar entre ejecuciones.")
    if args.estricto and problemas:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
