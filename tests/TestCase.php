<?php

namespace Tests;

use Illuminate\Auth\GenericUser;
use Illuminate\Foundation\Testing\TestCase as BaseTestCase;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Hash;

abstract class TestCase extends BaseTestCase
{
    protected const ADMIN_EMAIL = 'giaovien@example.com';

    protected const ADMIN_PASSWORD = 'mat-khau-thu-nghiem';

    protected string $jobsRoot;

    protected function setUp(): void
    {
        parent::setUp();

        config([
            'auth.providers.users.email' => self::ADMIN_EMAIL,
            'auth.providers.users.password_hash' => Hash::make(self::ADMIN_PASSWORD),
        ]);

        // Each test gets its own job root; never touch the real storage/app/private.
        $this->jobsRoot = storage_path('framework/testing/timetable-jobs-'.bin2hex(random_bytes(4)));
        config(['timetable.temp_root' => $this->jobsRoot]);
    }

    protected function tearDown(): void
    {
        File::deleteDirectory($this->jobsRoot);
        parent::tearDown();
    }

    protected function admin(): GenericUser
    {
        return new GenericUser(['id' => 'admin', 'email' => self::ADMIN_EMAIL, 'password' => null, 'remember_token' => null]);
    }
}
