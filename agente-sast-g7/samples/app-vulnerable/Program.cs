// Muestra DELIBERADAMENTE vulnerable para la metodología SAST del Grupo 7 (datos sintéticos).
using BancoFicticio.Repositories;
using BancoFicticio.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddAuthentication();
builder.Services.AddAuthorization();
builder.Services.AddHttpClient();

builder.Services.AddScoped<CuentaRepository>();
builder.Services.AddScoped<TransferenciaRepository>();
builder.Services.AddScoped<ReporteRepository>();
builder.Services.AddScoped<CuentaService>();
builder.Services.AddScoped<TransferenciaService>();
builder.Services.AddScoped<DocumentoService>();
builder.Services.AddScoped<ReporteService>();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();

app.Run();
