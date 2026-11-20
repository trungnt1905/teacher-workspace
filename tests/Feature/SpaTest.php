<?php

namespace Tests\Feature;

use Tests\TestCase;

class SpaTest extends TestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        $this->withoutVite();
    }

    public function test_root_serves_the_spa_shell(): void
    {
        $this->get('/')
            ->assertOk()
            ->assertSee('<div id="app"></div>', false);
    }

    public function test_client_side_routes_serve_the_spa_shell(): void
    {
        $this->get('/lich-bao-giang')->assertOk()->assertSee('<div id="app"></div>', false);
        $this->get('/login')->assertOk();
    }

    public function test_api_paths_are_not_swallowed_by_the_spa_route(): void
    {
        $this->get('/api')->assertNotFound();
        $this->getJson('/api/v1/unknown')->assertNotFound()->assertHeader('Content-Type', 'application/json');
    }
}
