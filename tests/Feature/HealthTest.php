<?php

namespace Tests\Feature;

use Tests\TestCase;

class HealthTest extends TestCase
{
    public function test_health_endpoint_returns_ok(): void
    {
        $this->getJson('/api/v1/health')
            ->assertOk()
            ->assertJsonPath('status', 'ok')
            ->assertJsonStructure(['status', 'time']);
    }

    public function test_health_endpoint_does_not_require_authentication_or_database(): void
    {
        config(['database.default' => 'missing-connection']);

        $this->getJson('/api/v1/health')->assertOk();
    }

    public function test_private_storage_is_not_served_over_http(): void
    {
        $this->withoutVite();
        $secret = 'private-content-'.bin2hex(random_bytes(8));
        \Illuminate\Support\Facades\Storage::disk('local')->put('timetable-jobs/probe/result.xlsx', $secret);

        try {
            foreach (['/storage/timetable-jobs/probe/result.xlsx', '/timetable-jobs/probe/result.xlsx'] as $url) {
                $this->get($url)->assertDontSee($secret);
            }
        } finally {
            \Illuminate\Support\Facades\Storage::disk('local')->deleteDirectory('timetable-jobs/probe');
        }
    }

    public function test_unknown_api_route_returns_json_404(): void
    {
        $this->getJson('/api/v1/does-not-exist')
            ->assertNotFound()
            ->assertHeader('Content-Type', 'application/json');
    }
}
