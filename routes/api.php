<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\TimetableJobController;
use Illuminate\Support\Facades\Route;

// Prefix: /api/v1 (bootstrap/app.php). Endpoint list: DETAIL_DESIGN §9.1.
// The api group carries session + CSRF middleware (same-origin SPA).

Route::get('/health', HealthController::class)->name('health');

Route::prefix('auth')->group(function () {
    Route::post('/login', [AuthController::class, 'login'])->middleware('throttle:login')->name('auth.login');
    Route::middleware('auth')->group(function () {
        Route::post('/logout', [AuthController::class, 'logout'])->name('auth.logout');
        Route::get('/me', [AuthController::class, 'me'])->name('auth.me');
    });
});

Route::middleware('auth')->prefix('timetable/jobs')->name('timetable.jobs.')->group(function () {
    Route::post('/', [TimetableJobController::class, 'store'])->name('store');
    Route::get('/{job}', [TimetableJobController::class, 'show'])->name('show');
    Route::post('/{job}/analyze', [TimetableJobController::class, 'analyze'])->name('analyze');
    Route::post('/{job}/generate', [TimetableJobController::class, 'generate'])->name('generate');
    Route::get('/{job}/download', [TimetableJobController::class, 'download'])->name('download');
    Route::delete('/{job}', [TimetableJobController::class, 'destroy'])->name('destroy');
});
