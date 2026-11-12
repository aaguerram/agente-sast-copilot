using Microsoft.Extensions.DependencyInjection;
using RickMorty.Application.Interfaces;
using RickMorty.Infrastructure.Data;

namespace RickMorty.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services)
    {
        // Singleton: los JSON embebidos se leen una sola vez y quedan en memoria.
        services.AddSingleton<IRickMortyDataSource, RickMortyJsonDataSource>();
        return services;
    }
}
