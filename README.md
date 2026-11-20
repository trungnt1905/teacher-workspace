# Teacher Workspace

Ứng dụng web hỗ trợ công việc giáo viên tiểu học. Giai đoạn đầu (MVP): **đồng bộ lịch báo giảng** — lấy tên bài và
đồ dùng dạy học từ lịch báo giảng của một lớp khác, điền vào lịch báo giảng của lớp mình theo thời khóa biểu riêng,
giữ nguyên định dạng file Excel.

Thiết kế chi tiết: [docs/DETAIL_DESIGN.md](docs/DETAIL_DESIGN.md).

## Cấu trúc

Một ứng dụng Laravel phục vụ cả giao diện lẫn API (cùng domain):

| Thư mục | Nội dung |
|---|---|
| `app/`, `routes/`, `config/` | Laravel API (`/api/v1/*`), không dùng database ở MVP |
| `resources/js/` | Giao diện Vue 3 SPA (vue-router, pinia), build bằng Vite |
| `resources/views/app.blade.php` | Khung SPA, trả về cho mọi đường dẫn không phải `/api` |
| `python/` | Bộ xử lý Excel (openpyxl để đọc, sửa XML trực tiếp để ghi) |
| `docs/` | Tài liệu thiết kế, [hệ thống giao diện](docs/design-system.md), triển khai, kết quả Phase 0 |

## Yêu cầu

- PHP 8.3+ và Composer
- Node.js 20+ và npm
- Python 3.12+

## Cài đặt lần đầu

```sh
composer install
cp .env.example .env
php artisan key:generate
npm install

cd python
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python process_timetable.py check
```

Laravel tự dùng `python/.venv` nếu có (để trống `PYTHON_BINARY` trong `.env`).

**Tạo tài khoản đăng nhập** (chỉ có một tài khoản, không cần database):

```sh
php artisan admin:password      # nhập mật khẩu 2 lần, in ra dòng ADMIN_PASSWORD_HASH='...'
```

Thêm vào `.env`:

```dotenv
ADMIN_EMAIL=email-cua-ban@example.com
ADMIN_PASSWORD_HASH='$2y$12$...'   # giữ nguyên dấu nháy đơn
```

## Chạy local

Mở 2 terminal:

```sh
php artisan serve   # http://127.0.0.1:8000 — giao diện + API
npm run dev         # Vite: sửa code Vue là trình duyệt tự cập nhật
```

Mở http://127.0.0.1:8000 → menu *Lịch báo giảng* hiển thị trạng thái kết nối máy chủ.

Không cần `npm run dev` nếu chỉ muốn chạy bản build: `npm run build` rồi `php artisan serve`.

## Engine Excel (CLI)

Laravel gọi engine theo từng job (thư mục chứa `source.xlsx`, `target.xlsx`, `request.json`):

```sh
python/.venv/bin/python python/process_timetable.py list-weeks --job-dir <thư mục job>   # -> weeks.json
python/.venv/bin/python python/process_timetable.py analyze    --job-dir <thư mục job>   # -> analysis.json
python/.venv/bin/python python/process_timetable.py generate   --job-dir <thư mục job>   # -> generate.json + result.xlsx
```

Ví dụ `request.json`: `{"weeks": [8], "selected_subjects": ["Toán", "Tiếng Việt"], "manual_days_off": []}`.
Mã thoát: 0 thành công, 1 lỗi nghiệp vụ (chi tiết trong file JSON kết quả), 2 lỗi hệ thống. Chi tiết: mục 8.3–8.4 của tài liệu thiết kế.

## API

Tất cả dưới `/api/v1`, cùng domain với giao diện, dùng session cookie + CSRF (header `X-XSRF-TOKEN` lấy từ cookie `XSRF-TOKEN`).

| Method | Đường dẫn | Việc |
|---|---|---|
| POST | `/auth/login`, `/auth/logout` · GET `/auth/me` | Đăng nhập / đăng xuất / người dùng hiện tại |
| POST | `/timetable/jobs` | Upload `source_file`, `target_file` → tuần, môn |
| GET / DELETE | `/timetable/jobs/{id}` | Xem / xóa job |
| POST | `/timetable/jobs/{id}/analyze` | Phân tích, xem trước |
| POST | `/timetable/jobs/{id}/generate` | Tạo file kết quả |
| GET | `/timetable/jobs/{id}/download` | Tải file `.xlsx` |

Chi tiết request/response và mã lỗi: mục 9 của tài liệu thiết kế.

## Kiểm thử

```sh
php artisan test
python/.venv/bin/python -m pytest -q python
npm test            # Vitest (hàm xử lý của giao diện)
npm run build
```

## Tiến độ

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0 | Xác nhận đầu vào, test round-trip, prototype | ✅ |
| 1 | Khởi tạo repository (Laravel + Vue + Python trong một ứng dụng) | ✅ |
| 2 | Python Excel engine (`list-weeks`, `analyze`, `generate`) | ✅ |
| 3 | Laravel API: đăng nhập, upload, phân tích, tạo file, tải về | ✅ |
| 4 | Giao diện: đăng nhập, wizard 4 bước | ✅ |
| 5 | Deploy lên Render: https://teacher-workspace-lr8u.onrender.com ([docs/deployment.md](docs/deployment.md)) | ✅ |
| 6 | Bảo mật và nghiệm thu ([hướng dẫn sử dụng](docs/user-guide.md)) | ✅ (còn 2 mục chờ xác nhận, mục 17) |
