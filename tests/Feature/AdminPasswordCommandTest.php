<?php

namespace Tests\Feature;

use Tests\TestCase;

class AdminPasswordCommandTest extends TestCase
{
    public function test_prints_a_hash_line_for_env(): void
    {
        $this->artisan('admin:password')
            ->expectsQuestion('Mật khẩu mới (tối thiểu 10 ký tự)', 'mot-mat-khau-dai')
            ->expectsQuestion('Nhập lại mật khẩu', 'mot-mat-khau-dai')
            ->expectsOutputToContain("ADMIN_PASSWORD_HASH='\$2y\$")
            ->assertExitCode(0);
    }

    public function test_rejects_short_or_mismatched_password(): void
    {
        $this->artisan('admin:password')
            ->expectsQuestion('Mật khẩu mới (tối thiểu 10 ký tự)', 'ngan')
            ->assertExitCode(1);

        $this->artisan('admin:password')
            ->expectsQuestion('Mật khẩu mới (tối thiểu 10 ký tự)', 'mot-mat-khau-dai')
            ->expectsQuestion('Nhập lại mật khẩu', 'khac-hoan-toan')
            ->assertExitCode(1);
    }
}
