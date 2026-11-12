using Microsoft.Extensions.DependencyInjection;
using RickMorty.Application.Interfaces;
using RickMorty.Application.Services;

namespace RickMorty.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddScoped<ICharacterService, CharacterService>();
        services.AddScoped<IEpisodeService, EpisodeService>();
        services.AddScoped<ILocationService, LocationService>();
        return services;
    }
}
