<?php

use Illuminate\Support\Facades\Route;

// Vue SPA: every non-API path returns the same shell; vue-router handles the rest.
// /api/* is excluded so unknown API routes still return JSON 404.
Route::view('/{any?}', 'app')
    ->where('any', '^(?!api(/|$)).*$')
    ->name('spa');
