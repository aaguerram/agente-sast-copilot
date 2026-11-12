var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.SetIsOriginAllowed(_ => true)
     .AllowAnyHeader()
     .AllowCredentials()));                                                             // ESPERA dotnet-cors-inseguro
var app = builder.Build();
app.UseDeveloperExceptionPage();                                                        // ESPERA dotnet-developer-exception-page
app.UseSwagger();                                                                       // ESPERA dotnet-swagger-sin-entorno
app.UseSwaggerUI();                                                                     // ESPERA dotnet-swagger-sin-entorno
if (!app.Environment.IsDevelopment())
{
    app.MapOpenApi();                                                                   // ESPERA dotnet-swagger-sin-entorno
}
app.Run();
