#!/usr/bin/env python3
"""Pruebas de metodologia.py y de la ejecución de referencia de la muestra app-vulnerable.

    docker compose --profile agentes run --rm py agente-sast-g7/scripts/tests/test_metodologia.py

Comprueban que, sobre la muestra, CADA paso encuentra problemas (incluidos los esperados
del inventario) y que no hay hallazgos en código limpio.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import metodologia  # noqa: E402

MUESTRA = SCRIPTS.parent / "samples" / "app-vulnerable"
ESPERADO_DIR = MUESTRA / "esperado"
ESPERADO = json.loads((ESPERADO_DIR / "fallas-esperadas.json").read_text(encoding="utf-8"))

CODIGO_LIMPIO = '''
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

[Authorize]
[ApiController]
[Route("api/limpio")]
public class LimpioController : ControllerBase
{
    private readonly ILogger<LimpioController> _logger;
    public LimpioController(ILogger<LimpioController> logger) => _logger = logger;

    [HttpGet("{id}")]
    public IActionResult Obtener([FromRoute] int id)
    {
        // Process.Start, BinaryFormatter y "SELECT ... " + x solo aparecen en este comentario.
        _logger.LogInformation("Consulta id={Id}", id);
        using var cmd = new SqlCommand("SELECT Nombre FROM T WHERE Id = @id");
        cmd.Parameters.AddWithValue("@id", id);
        return LocalRedirect("/inicio");
    }
}
'''


class TestScript(unittest.TestCase):
    def test_inventario_ordena_por_riesgo(self):
        doc = metodologia.inventario(MUESTRA)
        niveles = {c["archivo"]: c["nivel"] for c in doc["candidatos"]}
        self.assertGreater(doc["total"], 0)
        for archivo in ESPERADO["ranking"]["alto"]:
            self.assertEqual(niveles.get(archivo), "Alto", archivo)
        for archivo in ESPERADO["ranking"]["bajo"]:
            self.assertEqual(niveles.get(archivo), "Bajo", archivo)
        puntajes = [c["puntaje"] for c in doc["candidatos"]]
        self.assertEqual(puntajes, sorted(puntajes, reverse=True))

    def test_entradas_esperadas(self):
        doc = metodologia.entradas(MUESTRA)
        encontrados = {(c["archivo"], c["parametro"], c["fuente"]) for c in doc["candidatos"]}
        for e in ESPERADO["entradas"]:
            self.assertIn((e["archivo"], e["parametro"], e["fuente"]), encontrados, e)

    def test_operaciones_esperadas(self):
        doc = metodologia.operaciones(MUESTRA)
        encontrados = {(c["archivo"], c["categoria"]) for c in doc["candidatos"]}
        for e in ESPERADO["operaciones"]:
            self.assertIn((e["archivo"], e["categoria"]), encontrados, e)
        self.assertTrue(all(c["cwe"].startswith("CWE-") for c in doc["candidatos"]))

    def test_codigo_limpio_sin_operaciones(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "LimpioController.cs").write_text(CODIGO_LIMPIO, encoding="utf-8")
            self.assertEqual(metodologia.operaciones(Path(d))["total"], 0)
            entradas = metodologia.entradas(Path(d))["candidatos"]
            self.assertEqual([(c["parametro"], c["fuente"]) for c in entradas], [("id", "ruta")])
            inv = metodologia.inventario(Path(d))["candidatos"][0]
            self.assertNotIn("controlador-sin-authorize", inv["senales"])

    def test_cli_todo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(metodologia.main(["todo", str(MUESTRA), "--dir", d]), 0)
            for paso in ("inventario", "entradas", "operaciones"):
                doc = json.loads((Path(d) / f"candidatos-{paso}.json").read_text(encoding="utf-8"))
                self.assertGreater(doc["total"], 0, paso)


MULTILINEA_VULNERABLE = '''
using Newtonsoft.Json;

public class Multilinea
{
    private static readonly JsonSerializerSettings Ajustes = new JsonSerializerSettings
    {
        TypeNameHandling = TypeNameHandling.Auto,
    };
    private JsonSerializerSettings _otros = new();

    public Multilinea()
    {
        _otros.TypeNameHandling = TypeNameHandling.Objects;
    }

    public object? Campo(string json)
    {
        return JsonConvert.DeserializeObject(
            json,
            Ajustes);
    }

    public object? Asignado(string json) =>
        JsonConvert.DeserializeObject(json, _otros);

    public List<string> Buscar(string titular)
    {
        var sql = "SELECT Nombre FROM Clientes "
                  + "WHERE Titular = '"
                  + titular + "'";
        var url = "https://ejemplo.invalid/" + titular; // "comentario con ; y // dentro"
        return Ejecutar(sql);
    }

    public void Ejecutar(string formato, string destino)
    {
        var p = Process
            .Start("/bin/exportar",
                   "--formato " + formato);
        var ruta = Path.Combine(
            "/datos",
            destino);
        File
            .WriteAllText(ruta, "x");
    }
}
'''

LIMPIO_RUTAS = '''
public class Limpio
{
    private const string Carpeta = "/var/app";

    public void Configurar(IWebHostEnvironment env)
    {
        var xml = Path.Combine(AppContext.BaseDirectory,
            $"{Assembly.GetExecutingAssembly().GetName().Name}.xml");
        var datos = Path.Combine(env.ContentRootPath, "Data", "personajes.json");
        var fija = Path.Combine(Carpeta, "config.json");
        var texto = "/* no es comentario */ // tampoco";
        var ajustes = new JsonSerializerSettings { TypeNameHandling = TypeNameHandling.None };
        var obj = JsonConvert.DeserializeObject<Dto>(texto, ajustes);
    }
}
'''


class TestAnalisisPorSentencias(unittest.TestCase):
    """Limitaciones corregidas: sentencias en varias líneas, configuración definida
    aparte y falsos positivos en rutas internas."""

    def operaciones(self, codigo):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Codigo.cs").write_text(codigo, encoding="utf-8")
            return metodologia.operaciones(Path(d))["candidatos"]

    def test_sentencias_multilinea_detectadas(self):
        ops = self.operaciones(MULTILINEA_VULNERABLE)
        por_categoria = {}
        for c in ops:
            por_categoria.setdefault(c["categoria"], []).append(c)
        self.assertIn("sql-dinamico", por_categoria)
        self.assertEqual(por_categoria["sql-dinamico"][0]["linea"], 29, "línea donde empieza el SQL")
        self.assertEqual([(c["linea"], c["confianza"]) for c in por_categoria["comando-sistema"]], [(38, "alta")])
        rutas = por_categoria["ruta-archivo"]
        self.assertEqual({c["linea"] for c in rutas}, {41, 44}, rutas)
        self.assertTrue(all(c["confianza"] == "alta" for c in rutas), rutas)

    def test_configuracion_insegura_definida_aparte(self):
        des = [c for c in self.operaciones(MULTILINEA_VULNERABLE) if c["categoria"] == "deserializacion"]
        self.assertEqual({c["linea"] for c in des}, {19, 25}, des)
        self.assertTrue(all(c["confianza"] == "alta" for c in des), des)
        self.assertIn("Ajustes", des[0]["detalle"])

    def test_configuracion_global_sin_llamada(self):
        codigo = ('services.AddControllers().AddNewtonsoftJson(o =>\n'
                  '    o.SerializerSettings.TypeNameHandling = TypeNameHandling.All);\n')
        des = self.operaciones(codigo)
        self.assertEqual([(c["categoria"], c["linea"], c["confianza"]) for c in des],
                         [("deserializacion", 2, "media")])

    def test_rutas_internas_y_constantes_no_se_reportan(self):
        self.assertEqual(self.operaciones(LIMPIO_RUTAS), [])

    def test_rickmorty_sin_rutas_de_alta_confianza(self):
        doc = metodologia.operaciones(SCRIPTS.parents[1] / "rickmorty-clean")
        altas = [c for c in doc["candidatos"] if c["categoria"] == "ruta-archivo" and c["confianza"] == "alta"]
        self.assertEqual(altas, [])

    def test_entradas_con_varios_atributos_y_restricciones(self):
        codigo = '''
[ApiController]
public class C : ControllerBase
{
    [HttpGet("{id:int}")]
    public IActionResult Get(
        [FromRoute] int id,
        [FromQuery][DefaultValue(1)] int page = 1,
        CancellationToken ct = default) => Ok();
}
'''
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "C.cs").write_text(codigo, encoding="utf-8")
            ent = metodologia.entradas(Path(d))["candidatos"]
        self.assertEqual([(c["parametro"], c["fuente"]) for c in ent], [("id", "ruta"), ("page", "query")])

    def test_todas_las_operaciones_llevan_confianza(self):
        for c in metodologia.operaciones(MUESTRA)["candidatos"]:
            self.assertIn(c["confianza"], ("alta", "media"), c)


class TestEjecucionReferencia(unittest.TestCase):
    """La ejecución de referencia (esperado/) cumple: cada paso encuentra problemas."""

    def cargar(self, nombre):
        return json.loads((ESPERADO_DIR / nombre).read_text(encoding="utf-8"))

    def test_cada_paso_tiene_hallazgos(self):
        for nombre, clave in [("ranking.json", "archivos"), ("entradas.json", "entradas"),
                              ("operaciones.json", "operaciones"), ("flujos.json", "flujos"),
                              ("gaps.json", "gaps"), ("validacion.json", "veredictos"),
                              ("priorizacion.json", "hallazgos"), ("remediacion.json", "recomendaciones")]:
            with self.subTest(paso=nombre):
                self.assertGreater(len(self.cargar(nombre)[clave]), 0)

    def test_flujos_esperados(self):
        ids = {f["id"] for f in self.cargar("flujos.json")["flujos"]}
        for f in ESPERADO["flujos_vulnerables"] + ESPERADO["flujos_saneados"]:
            self.assertIn(f, ids)
        multi = [f for f in self.cargar("flujos.json")["flujos"]
                 if len({p["archivo"] for p in f["camino"]}) >= 3]
        self.assertGreaterEqual(len(multi), 3, "al menos 3 flujos cruzan 3 archivos")

    def test_gaps_cubren_requisitos(self):
        cubiertos = {g["requisito"] for g in self.cargar("gaps.json")["gaps"]}
        for req in ESPERADO["gaps"]:
            self.assertIn(req, cubiertos)

    def test_devils_advocate_refuta_el_saneado(self):
        veredictos = {v["id_hallazgo"]: v["veredicto"] for v in self.cargar("validacion.json")["veredictos"]}
        for f in ESPERADO["flujos_saneados"]:
            self.assertEqual(veredictos.get(f), "refutado", f)
        for f in ESPERADO["flujos_vulnerables"]:
            self.assertEqual(veredictos.get(f), "sobrevive", f)
        self.assertNotIn("F-11", {h["id_hallazgo"] for h in self.cargar("priorizacion.json")["hallazgos"]})

    def test_remediacion_trazable(self):
        priorizados = {h["id_hallazgo"] for h in self.cargar("priorizacion.json")["hallazgos"]}
        remediados = {r["id_hallazgo"] for r in self.cargar("remediacion.json")["recomendaciones"]}
        self.assertEqual(priorizados, remediados)


class TestComparadorEsperado(unittest.TestCase):
    """comparar_esperado.py: lo usan ./scripts/agente.sh demo y la skill /demo."""

    def ejecutar(self, *args):
        import subprocess
        return subprocess.run([sys.executable, str(SCRIPTS / "comparar_esperado.py"), *args],
                              capture_output=True, text=True, check=False)

    def test_referencia_contra_si_misma_estricto(self):
        r = self.ejecutar("--actual", str(ESPERADO_DIR), "--esperado", str(ESPERADO_DIR), "--estricto")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("FALTAN", r.stdout)

    def test_candidatos_actuales_cubren_fallas(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(metodologia.main(["todo", str(MUESTRA), "--dir", tmp]), 0)
            r = self.ejecutar("--actual", tmp, "--esperado", str(ESPERADO_DIR), "--estricto")
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("5/5 OK", r.stdout)

    def test_paso_vacio_falla_en_estricto(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "flujos.json").write_text(json.dumps({"ruta": "x", "flujos": []}), encoding="utf-8")
            r = self.ejecutar("--actual", tmp, "--esperado", str(ESPERADO_DIR), "--estricto")
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn("!", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
