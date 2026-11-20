# Hệ thống giao diện (Design system)

Mục tiêu: mọi màn hình — hiện tại và sau này — có **cùng màu sắc, cùng kiểu thành phần, cùng bố cục**. Khi thêm
chức năng mới, chỉ ghép các thành phần có sẵn; khi muốn đổi màu thương hiệu, chỉ sửa một file.

Phong cách: nền xám nhạt, nội dung đặt trên **thẻ trắng bo góc**, viền mảnh, bóng rất nhẹ; chữ Inter; icon nét mảnh
[Lucide](https://lucide.dev/icons) (`lucide-vue-next`).

## 1. File

| File | Nội dung |
|---|---|
| [`resources/css/tokens.css`](../resources/css/tokens.css) | **Nguồn duy nhất** của màu, bo góc, bóng, khoảng cách, cỡ chữ |
| [`resources/css/base.css`](../resources/css/base.css) | Reset, font, tiêu đề, focus |
| [`resources/css/components.css`](../resources/css/components.css) | Class dùng chung: `.btn`, `.card`, `.pill`, `.callout`, `.icon-tile`, `.field`, `.input`, `.progress-*`, bảng |
| [`resources/js/components/ui/`](../resources/js/components/ui) | Khối Vue dùng chung: `PageHeader`, `AppPanel` |
| [`tests/js/design-system.test.js`](../tests/js/design-system.test.js) | Test chặn màu viết cứng và token sai tên |

## 2. Màu

Token có 2 lớp:

1. **Bảng màu gốc** (`--gray-*`, `--blue-*`, `--red-*`, `--green-*`, `--amber-*`): chỉ dùng **bên trong `tokens.css`**.
2. **Màu theo vai trò** (`--color-*`): component **chỉ được dùng lớp này**.

Đổi màu thương hiệu = sửa bảng màu gốc hoặc phần gán trong `tokens.css`; không phải sửa component nào.

| Vai trò | Token | Dùng cho |
|---|---|---|
| Nền trang | `--color-bg` | Nền toàn trang (xám nhạt) |
| Bề mặt | `--color-surface`, `--color-surface-muted`, `--color-surface-sunken` | Thẻ, ô nhập / vùng phụ trong thẻ / thanh tiến độ, nhãn trung tính |
| Viền | `--color-border`, `--color-border-strong` | Viền thẻ, đường kẻ / viền nút phụ, ô nhập |
| Chữ | `--color-text`, `--color-text-secondary`, `--color-text-muted`, `--color-text-subtle`, `--color-text-inverse` | Tiêu đề / nội dung / gợi ý, nhãn / bị vô hiệu / chữ trên nền đậm |
| **Primary (xanh dương)** | `--color-primary` (+ `-strong`, `-soft`, `-muted`, `-border`) | **Lựa chọn, đang chọn, tiến độ, liên kết**, bước hiện tại |
| **Action (đỏ)** | `--color-action` (+ `-hover`, `-soft`) | **Nút hành động chính của màn hình** (mỗi màn tối đa 1 nút đỏ nổi bật) |
| Success (xanh lá) | `--color-success` (+ `-soft`, `-surface`, `-border`, `-text`) | Hoàn tất, "Điền", file hợp lệ |
| Warning (cam) | `--color-warning` (+ `-strong`, `-soft`, `-surface`, `-border`, `-text`) | Cần giáo viên chú ý: bỏ qua, ngày nghỉ, việc điền tay |
| Danger (đỏ đậm) | `--color-danger` (+ `-soft`, `-border`, `-text`) | Lỗi, không xử lý được |

Quy tắc:

- **Xanh = trạng thái/lựa chọn, đỏ = hành động.** Không dùng đỏ cho trạng thái chọn, không dùng xanh cho nút chính.
- Lỗi dùng `danger`, không dùng `action` (dù cùng tông đỏ).
- Cam (warning) báo "cần làm thêm", không phải lỗi.

## 3. Thang đo

| Nhóm | Token |
|---|---|
| Bo góc | `--radius-sm` 8px (nút, ô nhập) · `--radius` 12px (ô, dòng, hộp con) · `--radius-lg` 16px (thẻ) · `--radius-full` (nhãn tròn) |
| Bóng | `--shadow-sm` (nút phụ) · `--shadow` (thẻ) · `--shadow-hover` (thẻ bấm được khi rê chuột) · `--ring` (focus bàn phím) |
| Khoảng cách | `--space-1` 4 · `-2` 8 · `-3` 12 · `-4` 16 · `-5` 20 · `-6` 24 · `-8` 32 (px) |
| Cỡ chữ | `--text-xs` 12 · `-sm` 13 · `-base` 14 · `-md` 15 · `-lg` 18 · `-xl` 22 (px) |
| Bố cục | `--layout-max` 1240px · `--sidebar-width` 320px |

## 4. Thành phần dùng chung

### Nút

```html
<button class="btn btn-primary">Tạo file <ChevronRight /></button>      <!-- hành động chính (đỏ) -->
<button class="btn btn-secondary"><ChevronLeft /> Quay lại</button>   <!-- phụ, quay lại -->
<button class="btn btn-ghost"><Copy /> Sao chép</button>              <!-- công cụ -->
<button class="btn btn-link">Chọn tất cả</button>                     <!-- liên kết trong dòng -->
<a class="btn btn-primary btn-lg" href="…">Tải file Excel</a>          <!-- to hơn -->
```

Icon trong nút: 18px (tự động). Nút "tiếp" có `ChevronRight` bên phải, nút "quay lại" có `ChevronLeft` bên trái.

### Thẻ, ô icon, nhãn, thông báo

```html
<div class="card">…</div>
<span class="icon-tile"><FileSpreadsheet /></span>       <!-- biến thể: .blue .green -->
<span class="pill green"><Check /> Điền</span>           <!-- biến thể: .blue .green .amber .red -->
<p class="callout warn"><AlertTriangle /><span>…</span></p>   <!-- biến thể: .error .warn .success -->
<p class="eyebrow">Bước 2 · Chọn tuần</p>                <!-- tiêu đề nhỏ viết hoa -->
<label class="field">Email <input class="input" /></label>
<div class="progress-track"><div class="progress-fill" style="width: 50%"></div></div>
```

### Khối Vue

**`PageHeader`** — thẻ đầu trang của một chức năng:

```vue
<PageHeader title="Đồng bộ lịch báo giảng" badge="4 bước" subtitle="lbg.xlsx → lop5b.xlsx">
  <template #icon><FileSpreadsheet /></template>
  <!-- bên phải: tiến độ, đồng hồ, nút… -->
</PageHeader>
```

**`AppPanel`** — thẻ nội dung chuẩn:

```vue
<AppPanel eyebrow="Bước 2 · Chọn tuần và môn" title="Đồng bộ tuần nào, môn nào?" description="…">
  <template #aside><span class="pill green">7 môn điền</span></template>
  …nội dung…
  <template #footer>
    <button class="btn btn-secondary"><ChevronLeft /> Quay lại</button>
    <span class="muted small">1 tuần · 8 môn</span>
    <button class="btn btn-primary">Tiếp tục <ChevronRight /></button>
  </template>
</AppPanel>
```

## 5. Bố cục màn hình chức năng

```
┌ Topbar (logo · menu · tài khoản) ─────────────────────────────┐
│ PageHeader: [icon] Tiêu đề (nhãn) · mô tả      tiến độ · nút  │
├───────────────────────────────────────────┬───────────────────┤
│ AppPanel (nội dung chính)                 │ Cột phụ 320px     │
│   eyebrow · tiêu đề · mô tả               │  thẻ trạng thái   │
│   …                                       │  thẻ thông tin    │
│   ─────────────────────────────────────── │  thẻ hướng dẫn    │
│   [Quay lại]      ghi chú       [Chính →] │                   │
└───────────────────────────────────────────┴───────────────────┘
```

- Rộng tối đa `--layout-max`; cửa sổ hẹp hơn 960px thì cột phụ xuống dưới. Không có bố cục riêng cho điện thoại.
- Lưới chọn (ví dụ ô tuần) dùng ô vuông bo `--radius`: trắng = chọn được, xanh = đang chọn, viền nét đứt + chấm màu = không chọn được; luôn kèm chú thích màu.
- Danh sách lựa chọn (môn) dùng dòng/ô có ô tích ở đầu, nền `--color-primary-soft` khi chọn.

## 6. Quy tắc khi làm màn hình mới

1. **Không viết mã màu** (`#…`, `rgb()`) trong component — dùng `--color-*`. Test `npm test` sẽ báo lỗi.
2. Không dùng token bảng màu gốc (`--blue-500`…) trong component. Thiếu vai trò màu → thêm token `--color-*` mới vào `tokens.css` và ghi vào bảng ở mục 2.
3. Ưu tiên class/khối dùng chung; chỉ viết CSS riêng (`<style scoped>`) cho bố cục đặc thù của màn hình đó, dùng `--space-*`, `--radius*`, `--text-*`.
4. Mỗi màn hình tối đa một nút `btn-primary` nổi bật.
5. Thông báo cho giáo viên bằng tiếng Việt, nói rõ việc cần làm tiếp.
6. **Chỉ thiết kế cho máy tính** (trình duyệt laptop/PC). Không làm giao diện riêng cho điện thoại; chỉ cần bố cục không vỡ khi cửa sổ trình duyệt hẹp (dưới 960px cột phụ xuống dưới).
