#!/usr/bin/env python3
"""Pruebas de la base de conocimiento (agente-sast-g7/kb/) y de su uso en los scripts.

    docker compose --profile agentes run --rm py agente-sast-g7/scripts/tests/test_kb.py
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import kb  # noqa: E402
import metodologia  # noqa: E402
import normalizar_sarif  # noqa: E402

KB_DIR = SCRIPTS.parent / "kb"
ESPERADO_DIR = SCRIPTS.parent / "samples" / "app-vulnerable" / "esperado"


class TestKbCwe(unittest.TestCase):
    def test_normalizar_cwe(self):
        self.assertEqual(kb.normalizar_cwe("CWE-798: Use of Hard-coded Credentials"), "CWE-798")
        self.assertEqual(kb.normalizar_cwe("cwe_89"), "CWE-89")
        self.assertEqual(kb.normalizar_cwe("CWE:79"), "CWE-79")
        self.assertEqual(kb.normalizar_cwe(22), "CWE-22")
        self.assertEqual(kb.normalizar_cwe("sin cwe"), "")
        self.assertEqual(kb.normalizar_cwe(None), "")

    def test_catalogo_oficial(self):
        doc = json.loads((KB_DIR / "cwe-owasp.json").read_text(encoding="utf-8"))
        self.assertGreater(doc["total_debilidades"], 900)
        self.assertEqual(doc["vistas"]["owasp_2021"]["id"], "CWE-1344")

    def test_mapeo_owasp_2021(self):
        casos = {"CWE-89": "A03:2021", "CWE-78": "A03:2021", "CWE-639": "A01:2021",
                 "CWE-22": "A01:2021", "CWE-502": "A08:2021", "CWE-918": "A10:2021",
                 "CWE-798": "A07:2021", "CWE-532": "A09:2021", "CWE-434": "A04:2021"}
        for cwe, owasp in casos.items():
            self.assertTrue(kb.owasp_de(cwe).startswith(owasp), (cwe, kb.owasp_de(cwe)))

    def test_owasp_hereda_del_padre(self):
        # CWE-1284 (validación de cantidades) no está en la vista; hereda de CWE-20.
        self.assertEqual(kb.owasp_de("CWE-1284", heredar=False), "")
        self.assertTrue(kb.owasp_de("CWE-1284").startswith("A03:2021"))

    def test_uso_de_mapeo(self):
        self.assertEqual(kb.buscar_cwe("CWE-89")["uso"], "Allowed")
        self.assertIn(kb.buscar_cwe("CWE-20")["uso"], {"Discouraged", "Prohibited"})
        self.assertIsNone(kb.buscar_cwe("CWE-999999"))


class TestCheatSheets(unittest.TestCase):
    def test_indice_coherente(self):
        doc = json.loads((KB_DIR / "cheatsheets.json").read_text(encoding="utf-8"))
        for cwe, hojas in doc["por_cwe"].items():
            self.assertIsNotNone(kb.buscar_cwe(cwe), cwe)
            for h in hojas:
                self.assertIn(h, doc["hojas"], (cwe, h))
        for url in doc["hojas"].values():
            self.assertTrue(url.startswith("https://cheatsheetseries.owasp.org/cheatsheets/"), url)

    def test_cheatsheets_de(self):
        self.assertEqual(kb.cheatsheets_de("CWE-89")[0]["nombre"], "SQL_Injection_Prevention")
        # CWE-1284 no tiene hoja propia: hereda la de su padre CWE-20 (Input Validation).
        self.assertEqual(kb.cheatsheets_de("CWE-1284")[0]["nombre"], "Input_Validation")


class TestAsvs(unittest.TestCase):
    def test_requisitos_con_id_y_atribucion(self):
        texto = (KB_DIR / "asvs-requisitos.md").read_text(encoding="utf-8")
        self.assertIn("CC BY-SA 4.0", texto)
        ids = re.findall(r"\*\*ASVS-(V\d+\.\d+\.\d+)\*\*", texto)
        self.assertGreater(len(ids), 100)
        self.assertEqual(len(ids), len(set(ids)))
        for clave in ("V8.2.2", "V6.", "V1.2.", "V5.", "V16."):
            self.assertTrue(any(i.startswith(clave) for i in ids), clave)


def sarif(reglas, resultados):
    return {"runs": [{"tool": {"driver": {"name": "x", "rules": reglas}}, "results": resultados}]}


class TestNormalizarSarif(unittest.TestCase):
    def test_semgrep_etiqueta_completa_y_owasp_2021(self):
        doc = sarif([{"id": "r1", "properties": {"tags": [
            "CWE-798: Use of Hard-coded Credentials",
            "OWASP-A02:2017 - Broken Authentication",
            "OWASP-A07:2021 - Identification and Authentication Failures"]}}],
            [{"ruleId": "r1", "level": "error"}])
        h = normalizar_sarif.normalizar(doc)["hallazgos"][0]
        self.assertEqual(h["cwe"], "CWE-798")
        self.assertEqual(h["owasp"], "A07:2021-Identification and Authentication Failures")

    def test_owasp_desde_kb_si_falta(self):
        doc = sarif([{"id": "r2", "properties": {"tags": ["CWE-89"]}}], [{"ruleId": "r2"}])
        h = normalizar_sarif.normalizar(doc)["hallazgos"][0]
        self.assertEqual(h["cwe"], "CWE-89")
        self.assertTrue(h["owasp"].startswith("A03:2021"))

    def test_regla_dotnet_sin_etiquetas(self):
        doc = sarif([{"id": "CA2100"}], [{"ruleId": "CA2100", "level": "warning"}])
        h = normalizar_sarif.normalizar(doc)["hallazgos"][0]
        self.assertEqual(h["cwe"], "CWE-89")
        self.assertTrue(h["owasp"].startswith("A03:2021"))

    def test_sin_cwe(self):
        doc = sarif([{"id": "r3"}], [{"ruleId": "r3"}])
        h = normalizar_sarif.normalizar(doc)["hallazgos"][0]
        self.assertEqual((h["cwe"], h["owasp"]), ("", ""))


class TestValidarCweOwasp(unittest.TestCase):
    def test_referencia_sin_avisos_de_cwe(self):
        hallazgos = json.loads((ESPERADO_DIR / "priorizacion.json").read_text(encoding="utf-8"))["hallazgos"]
        errores, avisos = metodologia.validar_cwe_owasp(hallazgos)
        self.assertEqual(errores, [])
        self.assertEqual(avisos, [])

    def test_cwe_inexistente_y_owasp_distinto(self):
        errores, avisos = metodologia.validar_cwe_owasp([
            {"id_hallazgo": "X-1", "cwe": "CWE-999999", "owasp": ""},
            {"id_hallazgo": "X-2", "cwe": "CWE-89", "owasp": "A01:2021-Broken Access Control"},
            {"id_hallazgo": "X-3", "cwe": "CWE-20", "owasp": "A03:2021-Injection"},
        ])
        self.assertTrue(any("X-1" in e for e in errores))
        self.assertTrue(any("X-2" in a and "no coincide" in a for a in avisos))
        self.assertTrue(any("X-3" in a and "Discouraged" in a for a in avisos))

    def test_validar_corrida_falla_con_cwe_inventado(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            for f in ESPERADO_DIR.glob("*.json"):
                shutil.copy(f, tmp)
            f = Path(tmp) / "priorizacion.json"
            doc = json.loads(f.read_text(encoding="utf-8"))
            doc["hallazgos"][0]["cwe"] = "CWE-999999"
            f.write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(metodologia.main(["validar", tmp]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
