<?php

use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Hash;

// Generates the ADMIN_PASSWORD_HASH value for .env / Render (DETAIL_DESIGN §12.1).
// The password is read interactively and never echoed or logged.
Artisan::command('admin:password', function () {
    $password = $this->secret('Mật khẩu mới (tối thiểu 10 ký tự)');
    if (mb_strlen((string) $password) < 10) {
        $this->error('Mật khẩu phải có ít nhất 10 ký tự.');

        return 1;
    }
    if ($this->secret('Nhập lại mật khẩu') !== $password) {
        $this->error('Hai lần nhập không khớp.');

        return 1;
    }

    $hash = Hash::make($password);
    $this->line('Thêm dòng sau vào .env (giữ nguyên dấu nháy đơn), hoặc dán phần giá trị vào Render Environment:');
    $this->newLine();
    $this->line("ADMIN_PASSWORD_HASH='{$hash}'");

    return 0;
})->purpose('Tạo mã băm mật khẩu cho tài khoản giáo viên');
