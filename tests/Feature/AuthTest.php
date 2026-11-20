<?php

namespace Tests\Feature;

use Tests\TestCase;

class AuthTest extends TestCase
{
    public function test_login_me_logout(): void
    {
        $this->postJson('/api/v1/auth/login', ['email' => self::ADMIN_EMAIL, 'password' => self::ADMIN_PASSWORD])
            ->assertOk()
            ->assertJsonPath('data.email', self::ADMIN_EMAIL);

        $this->getJson('/api/v1/auth/me')->assertOk()->assertJsonPath('data.email', self::ADMIN_EMAIL);

        $this->postJson('/api/v1/auth/logout')->assertOk();
        $this->getJson('/api/v1/auth/me')->assertUnauthorized();
    }

    public function test_email_is_case_insensitive(): void
    {
        $this->postJson('/api/v1/auth/login', ['email' => strtoupper(self::ADMIN_EMAIL), 'password' => self::ADMIN_PASSWORD])
            ->assertOk();
    }

    public function test_wrong_password_is_rejected(): void
    {
        $this->postJson('/api/v1/auth/login', ['email' => self::ADMIN_EMAIL, 'password' => 'sai-mat-khau'])
            ->assertStatus(422)
            ->assertJsonPath('success', false)
            ->assertJsonPath('error.code', 'INVALID_CREDENTIALS');
        $this->getJson('/api/v1/auth/me')->assertUnauthorized();
    }

    public function test_unconfigured_account_cannot_log_in(): void
    {
        config(['auth.providers.users.password_hash' => null]);

        $this->postJson('/api/v1/auth/login', ['email' => self::ADMIN_EMAIL, 'password' => self::ADMIN_PASSWORD])
            ->assertStatus(422);
    }

    public function test_login_is_rate_limited(): void
    {
        for ($i = 0; $i < 5; $i++) {
            $this->postJson('/api/v1/auth/login', ['email' => self::ADMIN_EMAIL, 'password' => 'sai'])->assertStatus(422);
        }

        $this->postJson('/api/v1/auth/login', ['email' => self::ADMIN_EMAIL, 'password' => self::ADMIN_PASSWORD])
            ->assertStatus(429)
            ->assertJsonPath('error.code', 'TOO_MANY_ATTEMPTS');
    }

    public function test_validation_errors_use_api_error_format(): void
    {
        $this->postJson('/api/v1/auth/login', [])
            ->assertStatus(422)
            ->assertJsonPath('error.code', 'VALIDATION_FAILED')
            ->assertJsonStructure(['error' => ['details' => ['email', 'password']]]);
    }

    public function test_guest_gets_401_json(): void
    {
        $this->getJson('/api/v1/auth/me')
            ->assertUnauthorized()
            ->assertExactJson(['success' => false, 'error' => [
                'code' => 'UNAUTHENTICATED', 'message' => 'Vui lòng đăng nhập.', 'details' => [],
            ]]);
    }
}
