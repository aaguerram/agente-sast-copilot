// Muestra DELIBERADAMENTE vulnerable (datos sintéticos).
using Newtonsoft.Json;

namespace BancoFicticio.Services;

public class DocumentoService
{
    private const string Carpeta = "/var/banco/documentos";

    public string Guardar(string nombreArchivo, byte[] contenido)
    {
        // El nombre lo manda el cliente.
        var ruta = Path.Combine(Carpeta, nombreArchivo);
        File.WriteAllBytes(ruta, contenido);
        return ruta;
    }

    public byte[] Leer(string nombre)
    {
        var ruta = Path.Combine(Carpeta, nombre);
        return File.ReadAllBytes(ruta);
    }

    public object? Importar(Stream contenido)
    {
        using var lector = new StreamReader(contenido);
        // El JSON del cliente decide qué tipo .NET se instancia.
        var ajustes = new JsonSerializerSettings { TypeNameHandling = TypeNameHandling.All };
        return JsonConvert.DeserializeObject(lector.ReadToEnd(), ajustes);
    }
}
