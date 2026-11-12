#!/usr/bin/env python3
"""Valida los archivos de GitHub Copilot del repo (hook de pre-commit `copilot-frontmatter`).

- `.github/agents/*.agent.md`: YAML válido, `description`, herramientas portables entre los
  arneses Copilot y Local (execute, read, edit, search, agent, web, todo), sin campos que el
  arnés Copilot no acepta (handoffs, agents, argument-hint, advancedOptions) y con el bloque
  "Si el usuario no da detalles".
- `.github/skills/<nombre>/SKILL.md`: `name` igual a la carpeta (minúsculas, números y
  guiones), `description` de 1 a 1024 caracteres, solo campos conocidos y referencias a
  archivos que existen.
- `.github/prompts/*.prompt.md`: cada prompt tiene una skill con el mismo nombre y un
  `agent` que existe.

Uso: python tools/copilot/validar_frontmatter.py [raíz del repo]
"""
import re
import sys

import yaml
from pathlib import Path
raiz = Path(sys.argv[1] if len(sys.argv) > 1 else "."); errores = []
def fm(p):
    t = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m: errores.append(f"{p}: sin frontmatter"); return {}, t
    try: d = yaml.safe_load(m.group(1)) or {}
    except Exception as e: errores.append(f"{p}: YAML inválido: {e}"); return {}, t
    return d, t[m.end():]
agentes = {}
for p in sorted((raiz/".github/agents").glob("*.agent.md")):
    d, cuerpo = fm(p); agentes[d.get("name", p.name[:-9])] = p
    if not d.get("description"): errores.append(f"{p}: falta description")
    for k in ("handoffs", "agents", "argument-hint", "advancedOptions"):
        if k in d: errores.append(f"{p}: campo no soportado por el arnés Copilot: {k}")
    tools = d.get("tools")
    if tools is not None:
        malos = [t for t in tools if t not in {"execute","read","edit","search","agent","web","todo"}]
        if malos: errores.append(f"{p}: tools no portables: {malos}")
    if "runSubagent" in cuerpo: errores.append(f"{p}: menciona runSubagent")
    if "Si el usuario no da detalles" not in cuerpo: errores.append(f"{p}: falta bloque 'Si el usuario no da detalles'")
skills = {}
for p in sorted((raiz/".github/skills").glob("*/SKILL.md")):
    d, cuerpo = fm(p); n = d.get("name"); skills[n] = p
    if n != p.parent.name: errores.append(f"{p}: name '{n}' != carpeta '{p.parent.name}'")
    if not n or not re.fullmatch(r"[a-z0-9-]{1,64}", n): errores.append(f"{p}: name inválido")
    desc = d.get("description") or ""
    if not desc or len(desc) > 1024: errores.append(f"{p}: description vacía o > 1024 ({len(desc)})")
    extra = set(d) - {"name","description","argument-hint","user-invocable","disable-model-invocation","context","license","compatibility","metadata","allowed-tools"}
    if extra: errores.append(f"{p}: campos desconocidos {extra}")
    for ref in re.findall(r"\.github/(?:agents|skills)/[\w./-]+?\.md", cuerpo):
        if not (raiz/ref).exists(): errores.append(f"{p}: referencia inexistente {ref}")
    for ref in re.findall(r"`(\./scripts/[\w.-]+|agente-sast-g7/[\w./-]+\.(?:py|md))", cuerpo):
        if not (raiz/ref).exists(): errores.append(f"{p}: ruta inexistente {ref}")
for p in sorted((raiz/".github/prompts").glob("*.prompt.md")):
    d, cuerpo = fm(p); n = d.get("name")
    if not d.get("description"): errores.append(f"{p}: falta description")
    if d.get("agent") and d["agent"] not in agentes: errores.append(f"{p}: agent inexistente {d['agent']}")
    if n not in skills: errores.append(f"{p}: no hay skill '{n}'")
for p in list((raiz/".github/agents").glob("*.md")):
    for ref in re.findall(r"\.github/(?:agents|skills)/[\w./-]+?\.md", p.read_text(encoding="utf-8")):
        if not (raiz/ref).exists(): errores.append(f"{p}: referencia inexistente {ref}")
print(f"agentes={len(agentes)} skills={len(skills)} prompts={len(list((raiz/'.github/prompts').glob('*.prompt.md')))}")
print("\n".join(errores) or "OK: frontmatter válido")
sys.exit(1 if errores else 0)
