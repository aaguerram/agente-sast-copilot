using System.Reflection;
using Microsoft.OpenApi;
using RickMorty.Application;
using RickMorty.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Rick and Morty — API REST (Clean Architecture)",
        Version = "v1",
        Description = """
            API REST sobre los datos de Rick and Morty con **data quemada**: lee las respuestas
            de la API GraphQL (https://rickandmortyapi.com/graphql) capturadas en JSON dentro de
            Infrastructure. No hace llamadas externas en tiempo de ejecución.

            **Ejemplos de consumo:**
            - `GET /api/characters?page=1&name=rick` — personajes filtrados por nombre
            - `GET /api/characters/1` — personaje por id (Rick Sanchez)
            - `GET /api/episodes?page=1` — episodios paginados
            - `GET /api/episodes/1` — episodio por id (Pilot)
            - `GET /api/episodes/1/characters` — personajes que aparecen en un episodio
            - `GET /api/locations?page=1&name=earth` — ubicaciones filtradas por nombre
            - `GET /api/locations/1` — ubicación por id (Earth C-137)
            - `GET /api/locations/1/residents` — residentes de una ubicación
            """,
    });

    var xml = Path.Combine(AppContext.BaseDirectory,
        $"{Assembly.GetExecutingAssembly().GetName().Name}.xml");
    if (File.Exists(xml)) options.IncludeXmlComments(xml);
});

// Capas (arquitectura limpia)
builder.Services.AddApplication();
builder.Services.AddInfrastructure();

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI(ui =>
{
    ui.SwaggerEndpoint("/swagger/v1/swagger.json", "Rick and Morty API v1");
    ui.RoutePrefix = string.Empty; // Swagger en la raíz: http://localhost:8080/
});

app.MapControllers();
app.Run();
