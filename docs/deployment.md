# Triển khai lên Render (gói Free)

Ứng dụng chạy thành **một Docker Web Service** trên Render: Nginx + PHP-FPM (Laravel, phục vụ cả giao diện Vue
lẫn API) + Python (xử lý Excel). Không cần database, không cần dịch vụ nào khác.

Cấu hình nằm trong repo: [`Dockerfile`](../Dockerfile), [`docker/`](../docker), [`render.yaml`](../render.yaml).

## Cần chuẩn bị (làm trên máy của bạn, một lần)

Chạy trong thư mục dự án:

```sh
php artisan key:generate --show     # -> APP_KEY, dạng base64:....
php artisan admin:password          # -> ADMIN_PASSWORD_HASH='$2y$12$...'
```

Ghi lại 3 giá trị:

| Biến | Giá trị |
|---|---|
| `APP_KEY` | Chuỗi `base64:...` vừa in ra |
| `ADMIN_EMAIL` | Email bạn dùng để đăng nhập |
| `ADMIN_PASSWORD_HASH` | Phần **bên trong** dấu nháy đơn, bắt đầu bằng `$2y$` (trên Render không cần dấu nháy) |

> Không commit các giá trị này vào repo. `APP_KEY` dùng để mã hóa cookie đăng nhập: đổi nó thì mọi phiên đăng nhập
> bị đăng xuất (không mất dữ liệu gì vì hệ thống không lưu dữ liệu lâu dài).

## Tạo service (lần đầu)

1. Push code lên GitHub (nhánh `main`).
2. Vào https://dashboard.render.com → **New** → **Blueprint**.
3. Chọn repo `teacher-workspace`. Render đọc `render.yaml` và đề xuất service `teacher-workspace` (Docker, Free, Singapore).
4. Render hỏi 3 biến bí mật `APP_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` → dán giá trị đã chuẩn bị.
5. Bấm **Apply**. Lần build đầu mất khoảng 5–10 phút.
6. Khi trạng thái là **Live**, mở địa chỉ dạng `https://teacher-workspace-xxxx.onrender.com` và đăng nhập.

`APP_URL` không cần khai báo: container tự dùng biến `RENDER_EXTERNAL_URL` do Render cung cấp.

## Cập nhật

`autoDeploy: true`: mỗi lần bạn push lên `main`, Render tự build và deploy lại. Trong lúc deploy, phiên đang xử lý
dở (file đã upload) sẽ mất — chỉ cần upload lại.

Đổi mật khẩu: chạy lại `php artisan admin:password`, vào Render → service → **Environment** → sửa
`ADMIN_PASSWORD_HASH` → **Save** (Render tự khởi động lại).

## Lưu ý của gói Free

- Không có request trong khoảng 15 phút thì service **ngủ**. Lần mở trang tiếp theo phải chờ khoảng 1 phút (trang
  trắng) — bình thường, không phải lỗi.
- Khi service ngủ hoặc deploy lại, các file tạm (file đã upload, file kết quả chưa tải) bị xóa. Giao diện sẽ báo
  "Phiên xử lý đã hết hạn…", chỉ cần upload lại.
- Giới hạn: khoảng 512MB RAM. Đo thực tế với file mẫu: dưới 100MB.
- Hạn mức và điều kiện gói Free có thể thay đổi; kiểm tra https://render.com/pricing.

## Kiểm tra sau khi deploy

- `https://<địa-chỉ>/api/v1/health` trả `{"status":"ok",...}`.
- Đăng nhập, upload 2 file, xem trước, tạo file và tải về.
- Xem log: Render → service → **Logs**. Lỗi xử lý file có dòng `timetable.python_failed` kèm `job_id`.

## Chạy thử image trên máy (không bắt buộc)

```sh
docker build -t teacher-workspace:local .
docker run --rm -p 8090:10000 \
  -e APP_KEY="base64:..." \
  -e ADMIN_EMAIL="email@example.com" \
  -e ADMIN_PASSWORD_HASH='$2y$12$...' \
  -e SESSION_SECURE_COOKIE=false \
  teacher-workspace:local
# mở http://127.0.0.1:8090
```

`SESSION_SECURE_COOKIE=false` chỉ dùng khi chạy thử bằng `http://` trên máy; trên Render luôn là HTTPS nên giữ mặc
định `true`.

## Thành phần trong image

| Thành phần | Ghi chú |
|---|---|
| `node:20` (chỉ lúc build) | `npm ci && npm run build` → `public/build` |
| `composer:2` (chỉ lúc build) | `composer install --no-dev` |
| `php:8.3-fpm-bookworm` | Runtime: PHP-FPM, Nginx, Supervisor, Python 3.11 + venv `/opt/venv` |
| `docker/entrypoint.sh` | Kiểm tra 3 biến bắt buộc, tạo thư mục tạm, cache config/route/view, sinh cấu hình Nginx theo `PORT` |
| `docker/nginx.conf.template` | Upload tối đa 12MB/request, timeout 90s, cache asset 1 năm, chặn dotfile |
| `docker/php.ini`, `docker/php-fpm.conf` | Giới hạn upload, opcache, 4 worker, timeout 90s |
