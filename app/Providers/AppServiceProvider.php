<?php

namespace App\Providers;

use App\Auth\EnvUserProvider;
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        Auth::provider('env', fn ($app, array $config) => new EnvUserProvider(
            $app['hash'],
            $config['email'] ?? null,
            $config['password_hash'] ?? null,
        ));

        // DETAIL_DESIGN §12.1: 5 login attempts per minute per IP.
        RateLimiter::for('login', fn (Request $request) => Limit::perMinute(5)->by($request->ip()));
    }
}
