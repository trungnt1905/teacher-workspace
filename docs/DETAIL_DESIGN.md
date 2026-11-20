# Teacher Workspace

## Detail Design — Kiến trúc và đặc tả kỹ thuật MVP

- **Phiên bản tài liệu:** 1.9
- **Ngày:** 19/11/2026
- **Trạng thái:** Bản thiết kế đề xuất để triển khai MVP
- **Ngôn ngữ:** Tiếng Việt
- **Đối tượng đọc:** Product owner, developer, Claude Code

### Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung |
|---|---|---|
| 1.0 | 19/11/2026 | Bản đầu tiên. |
| 1.1 | 19/11/2026 | Giáo viên tự chuẩn bị sheet tuần bằng cách copy `MẪU` trong Excel, hệ thống chỉ ghi giá trị (bỏ việc copy sheet bằng code). Chốt quy tắc: nghỉ lễ, môn giáo viên bộ môn, sheet tuần đã có dữ liệu, ô nguồn trống, chỉ hỗ trợ `.xlsx`. Mismatch không còn chặn cả tuần mà chỉ bỏ qua môn bị lệch. Bổ sung: template profile, `meta.json`, hợp đồng Python ↔ Laravel, danh mục mã lỗi, phương án auth không cần database, cấu hình giới hạn upload/timeout. Sửa định dạng danh sách và bảng. |
| 1.2 | 19/11/2026 | Phase 0 với file mẫu `LBG_mau.xlsx`: chốt tọa độ ô (mục 8.2), danh sách tên môn thực tế, quy tắc nhận diện nghỉ. Kết quả test round-trip: openpyxl làm thay đổi định dạng cả các sheet không ghi → **đổi writer sang sửa trực tiếp XML** (mục 5.3). Thêm các câu hỏi mới ở mục 20.3. |
| 1.3 | 19/11/2026 | Chốt: giáo viên tích chọn môn cần đồng bộ, mặc định bỏ tích môn bộ môn (chữ đỏ); HĐTV/HĐTT là nhóm hoán đổi và được ghi cả cột D; tiết trống lẻ chỉ cảnh báo, không bỏ qua môn, không cần danh sách ngoại lệ; chỉ chữ "Nghỉ" hoặc cả buổi trống mới là nghỉ. |
| 1.4 | 19/11/2026 | Làm rõ: tiết **không có tên bài hoặc có chữ "Nghỉ" là tiết nghỉ** → môn đó không xử lý trong tuần và cảnh báo (thay quy tắc tiết trống của bản 1.3). Ghi nhận cách file thật đánh dấu ngày nghỉ (gộp `E:F` và để trống). Thêm `HĐTV/HĐTT` vào nhóm hoán đổi. Kết quả prototype đầy đủ trên `TUẦN 8.xlsx` và tuần nghỉ `TUẦN 7`. |
| 1.5 | 19/11/2026 | **Gộp giao diện vào Laravel:** Laravel ở thư mục gốc repo, Vue SPA trong `resources/js` (laravel-vite-plugin), Python trong `python/`. Bỏ Cloudflare Pages và Pages Function proxy; một Docker image trên Render phục vụ cả giao diện và API cùng origin. Viết lại mục 6, 7, 14; cập nhật auth (session guard chuẩn, không cần Sanctum), Docker multi-stage, kế hoạch Phase 5. |
| 1.6 | 19/11/2026 | Phase 2 hoàn thành: Python engine. Request dùng `selected_subjects` (môn được chọn) thay cho `excluded_subjects`; thêm trạng thái `skipped_empty_lesson`, trường `selectable`/`status`/`writes`; nhóm hoán đổi có `key`; thêm mã lỗi `SOURCE_WEEK_SHEET_MISSING`, `INVALID_REQUEST`, `NOTHING_TO_GENERATE`, `OUTPUT_VERIFY_FAILED`; thêm `defusedxml`. |
| 1.7 | 19/11/2026 | Phase 3 hoàn thành: Laravel API (auth một tài khoản từ env, upload/analyze/generate/download, quản lý job, định dạng lỗi thống nhất, mã lỗi mới), múi giờ Asia/Ho_Chi_Minh, lệnh `admin:password`. |
| 1.8 | 20/11/2026 | Phase 4 hoàn thành: giao diện đăng nhập và wizard 4 bước; upload trả thêm `days`; khôi phục job sau khi tải lại trang; Vitest cho frontend. |
| 1.9 | 20/11/2026 | Phase 5 (phần trong repo): Dockerfile, cấu hình `docker/`, `render.yaml`, `docs/deployment.md`; trust proxy; `PreventRequestForgery`; không log lỗi nghiệp vụ. Còn bước tạo service trên Render do người dùng làm. |

------------------------------------------------------------------------

# 1. Mục tiêu tài liệu

Tài liệu này mô tả thiết kế chi tiết cho Teacher Workspace — ứng dụng web hỗ trợ công việc giáo viên tiểu học. Giai đoạn đầu phục vụ một giáo viên sử dụng cá nhân, ưu tiên đưa chức năng **đồng bộ lịch báo giảng từ hai file Excel** lên Internet.

Tài liệu bao gồm:

1. Phạm vi sản phẩm và các quyết định nghiệp vụ đã thống nhất.
2. Kiến trúc triển khai online với Vue 3, Laravel API và Python.
3. Thiết kế frontend, backend, xử lý Excel và luồng upload/download.
4. Thiết kế API, cấu trúc mã nguồn, cấu hình môi trường.
5. Bảo mật, giới hạn gói miễn phí, xử lý lỗi và vận hành.
6. Kế hoạch triển khai từng giai đoạn và tiêu chí nghiệm thu.
7. Các điểm cần xác nhận khi có file Excel thực tế hoặc trước khi public.

Quy ước đánh dấu:

- **\[ĐÃ CHỐT\]**: người dùng đã xác nhận.
- **\[ĐỀ XUẤT\]**: phương án khuyến nghị, chưa được xác nhận tuyệt đối.
- **\[CẦN XÁC NHẬN\]**: phải xác định khi có workbook thực tế hoặc trước khi triển khai.

Không tự coi mục \[ĐỀ XUẤT\] hoặc \[CẦN XÁC NHẬN\] là yêu cầu đã chốt.

------------------------------------------------------------------------

# 2. Tổng quan sản phẩm

## 2.1. Tầm nhìn

Teacher Workspace là workspace trực tuyến giúp giáo viên quản lý và thực hiện các công việc chuyên môn, không chỉ là một chatbot AI.

Định hướng dài hạn:

- Quản lý lịch báo giảng và kế hoạch giảng dạy.
- Quản lý thư viện giáo án, tài liệu, sách, slide và học liệu.
- Hỗ trợ soạn giáo án, tiết dạy giỏi, dự giờ.
- Tạo phiếu học tập, câu hỏi, đề kiểm tra và PowerPoint.
- Hỗ trợ viết nhận xét học sinh, báo cáo và hồ sơ chuyên môn.
- Có thể mở rộng từ một giáo viên sang nhiều giáo viên hoặc trường học.

## 2.2. Đối tượng sử dụng giai đoạn đầu

- Một giáo viên tiểu học.
- Trước mắt sử dụng cá nhân, không cần quy trình phê duyệt nhiều cấp.
- Người dùng truy cập qua trình duyệt trên máy tính hoặc điện thoại.
- Giao diện và hướng dẫn sử dụng bằng tiếng Việt.

## 2.3. Nguyên tắc thiết kế

1. **MVP nhỏ, kiến trúc có đường mở rộng:** không xây dựng microservice hoặc database nếu chưa có nhu cầu thực tế.
2. **Nghiệp vụ xác định bằng code:** phân phối tiết học, đối chiếu môn, kiểm tra số lượng phải do Python xử lý theo quy tắc rõ ràng, không giao cho AI.
3. **Không phá vỡ file gốc:** file nguồn và file đích không bao giờ bị ghi đè; kết quả luôn là một file mới.
4. **Hệ thống chỉ ghi giá trị, không đụng định dạng:** sheet tuần do giáo viên chuẩn bị sẵn bằng cách copy sheet `MẪU` trong Excel. Hệ thống chỉ ghi giá trị vào các ô đã xác định, không copy sheet, không thay style.
5. **Có preview và kiểm tra trước khi xuất:** không tạo file kết quả âm thầm; mọi môn bị bỏ qua đều được báo rõ lý do.
6. **An toàn hơn đầy đủ:** khi không chắc chắn (lệch số tiết, ngày nghỉ, tên môn lạ), hệ thống bỏ qua phần đó và báo giáo viên tự điều chỉnh, không đoán.
7. **Bảo vệ dữ liệu giáo viên/học sinh:** không public file upload; không gửi dữ liệu học sinh đến AI trong MVP.
8. **Tách nghiệp vụ khỏi nhà cung cấp hạ tầng:** không để logic xử lý Excel phụ thuộc Render hay nhà cung cấp hosting.

------------------------------------------------------------------------

# 3. Phạm vi MVP

## 3.1. Chức năng nằm trong MVP

### A. Truy cập và đăng nhập

- Website online, có trang đăng nhập.
- Giai đoạn đầu chỉ cần một tài khoản được cấp trước.
- Các API nghiệp vụ phải yêu cầu xác thực.
- Không có chức năng tự đăng ký công khai.
- Có đăng xuất và hết hạn phiên đăng nhập.

### B. Đồng bộ lịch báo giảng Excel

- Hướng dẫn giáo viên chuẩn bị file đích (copy sheet `MẪU` thành các sheet tuần).
- Upload file nguồn và file đích.
- Đọc danh sách sheet tuần từ file nguồn và trạng thái sheet tuần tương ứng trong file đích.
- Chọn một hoặc nhiều tuần.
- Chọn các môn cần đồng bộ (mặc định loại trừ môn giáo viên bộ môn).
- Phân tích dữ liệu từng tuần: đối chiếu số tiết theo môn, phát hiện ngày nghỉ.
- Preview dữ liệu dự kiến và danh sách môn bị bỏ qua.
- Xác nhận xử lý.
- Tạo workbook kết quả để tải xuống.
- Giữ nguyên file nguồn và file đích.
- Dọn file tạm sau khi hoàn tất hoặc hết hạn.

### C. Theo dõi kết quả

- Hiển thị trạng thái xử lý.
- Hiển thị lỗi/cảnh báo theo tuần, ngày, môn.
- Hiển thị số lượng tiết nguồn và slot đích.
- Hiển thị danh sách môn giáo viên cần tự điền sau khi tải file.
- Cho phép tải file kết quả khi thành công.
- Không yêu cầu lưu lịch sử lâu dài ở giai đoạn đầu.

## 3.2. Ngoài phạm vi MVP

Chưa triển khai ở phiên bản đầu:

- Database nghiệp vụ.
- Quản lý nhiều tài khoản và phân quyền.
- Quản lý nhiều trường/lớp/năm học.
- Tự động copy sheet `MẪU` để tạo sheet tuần (xem mục 21).
- Tự động dồn bài sang tuần sau khi lệch số tiết (xem mục 21).
- Hỗ trợ file `.xls` hoặc định dạng khác `.xlsx`.
- Lưu thư viện giáo án dài hạn.
- Tìm kiếm semantic/vector.
- AI soạn giáo án.
- Tạo PowerPoint, Word hoặc đề kiểm tra.
- Quy trình duyệt giáo án.
- Đồng bộ Google Drive/OneDrive.
- Lịch sử xử lý lâu dài.
- Hàng đợi tác vụ phân tán.

Các chức năng này cần được thiết kế để có thể bổ sung, nhưng không làm tăng độ phức tạp của MVP.

------------------------------------------------------------------------

# 4. Các quyết định nghiệp vụ lịch báo giảng

Đây là phần quan trọng nhất của MVP.

## 4.1. Hai file Excel

Hệ thống nhận **hai workbook riêng biệt**, cả hai đều là `.xlsx` **\[ĐÃ CHỐT\]**:

1. **File nguồn:** lịch báo giảng của một lớp khác, đã có nội dung bài học.
2. **File đích:** lịch báo giảng của lớp người dùng, có thời khóa biểu riêng.

Hai file có cấu trúc bảng gần như giống hệt nhau. Khác biệt chủ yếu là dữ liệu trong các ô:

- Ngày tháng.
- Thứ tự môn học theo từng ngày/tiết.
- Tên bài.
- Đồ dùng dạy học.

**\[ĐÃ CHỐT\]** File nguồn và file đích có cùng bố cục, tọa độ ô cố định (đã xác nhận với file mẫu `LBG_mau.xlsx`: sheet `MẪU` + 9 sheet `TUẦN 1`…`TUẦN 9`, tất cả cùng vùng `A1:F36` và cùng 18 vùng gộp ô). Dùng **một parser và một template profile** (mục 8.2) cho cả hai file.

## 4.2. File nguồn

File nguồn cung cấp dữ liệu nội dung:

- Tuần.
- Ngày/thứ và ngày tháng.
- Buổi.
- Tiết.
- Môn.
- Tên bài.
- Đồ dùng dạy học.

File nguồn không quyết định thời khóa biểu của lớp đích.

## 4.3. File đích

File đích quyết định cấu trúc và thời khóa biểu đầu ra:

- Có sheet `MẪU` — mẫu chuẩn của lớp đích.
- Có các **sheet tuần do giáo viên tự tạo** bằng cách copy sheet `MẪU` trong Excel (mục 4.4).
- Thứ tự môn học theo từng ngày/tiết **trên mỗi sheet tuần** là thời khóa biểu của lớp đích cho tuần đó.
- Các vị trí môn học trên sheet tuần là các slot sẽ nhận nội dung.
- Giữ nguyên định dạng, cấu trúc và các thành phần của file đích.

## 4.4. Chuẩn bị sheet tuần — giáo viên thực hiện \[ĐÃ CHỐT\]

Hệ thống **không** tự copy sheet `MẪU`. Giáo viên chuẩn bị file đích trước khi upload:

1. Mở file đích bằng Excel.
2. Chuột phải sheet `MẪU` → *Move or Copy* → tích *Create a copy*.
3. Đổi tên bản sao theo tuần, ví dụ `TUẦN 12`.
4. Lặp lại cho các tuần muốn đồng bộ.
5. Nếu tuần nào có thời khóa biểu khác `MẪU`, giáo viên sửa trực tiếp môn học trên sheet tuần đó.
6. Lưu file và upload.

Lý do chọn cách này:

- Excel copy sheet giữ đầy đủ 100% định dạng, thiết lập in, ảnh, freeze panes… — điều mà `openpyxl.copy_worksheet()` không đảm bảo (mục 5.3).
- Hệ thống chỉ còn nhiệm vụ đọc và ghi giá trị ô, đơn giản và ít lỗi hơn.
- Giáo viên kiểm soát được thời khóa biểu từng tuần (đổi TKB giữa kỳ, tuần đặc biệt).
- Thao tác chỉ mất vài giây mỗi tuần.

Giao diện phải có hướng dẫn ngắn kèm hình minh họa cho bước này.

## 4.5. Trạng thái sheet tuần trong file đích \[ĐÃ CHỐT\]

Với mỗi tuần được chọn, hệ thống tìm sheet cùng số tuần trong file đích và phân loại:

| Trạng thái | Điều kiện | Hành động |
|---|---|---|
| `ready` | Có sheet tuần, mọi ô tên bài đều trống | Xử lý |
| `has_data` | Có sheet tuần, có ít nhất một ô tên bài đã có nội dung | **Không xử lý**, báo "Sheet TUẦN X đã có dữ liệu" |
| `missing` | Không có sheet tuần tương ứng | **Không xử lý**, báo "Chưa có sheet TUẦN X — hãy copy sheet MẪU" |
| `invalid_structure` | Sheet tuần không khớp cấu trúc template profile | **Không xử lý**, báo vị trí sai khác |

Ghi chú:

- So khớp sheet theo **số tuần** sau chuẩn hóa (mục 8.4), ví dụ `TUẦN 9` và `TUẦN 09` là cùng tuần.
- Nếu file đích có hai sheet cùng số tuần → lỗi `DUPLICATE_WEEK_SHEET`, không xử lý tuần đó.
- Quy tắc `has_data` cho phép làm việc tăng dần: giáo viên có thể upload file kết quả lần trước làm file đích cho lần sau; các tuần đã điền sẽ tự được bỏ qua.
- Muốn xử lý lại một tuần: giáo viên xóa sheet đó, copy lại từ `MẪU`.

## 4.6. Phân phối nội dung theo môn

**Không copy theo cùng số dòng hoặc cùng vị trí tiết của file nguồn.**

Thuật toán cho mỗi tuần:

1. Đọc các bản ghi tiết học trong tuần nguồn theo thứ tự xuất hiện.
2. Chuẩn hóa tên môn.
3. Xác định các ngày nghỉ (mục 4.8).
4. Loại các môn không đồng bộ (mục 4.9).
5. Gom bản ghi theo môn, giữ thứ tự xuất hiện trong từng môn.
6. Đọc các slot môn học trong sheet tuần đích theo thứ tự xuất hiện.
7. Gom slot theo môn, giữ thứ tự xuất hiện.
8. Với từng môn, kiểm tra điều kiện xử lý (mục 4.7, 4.8). Môn không đạt điều kiện → bỏ qua, ghi cảnh báo.
9. Môn đạt điều kiện → ghép lần lượt bản ghi nguồn thứ *i* vào slot đích thứ *i*.
10. Tên bài và đồ dùng luôn đi cùng một bản ghi.

Ví dụ minh họa:

**Nguồn — lớp 5A**

| Thứ | Tiết | Môn | Tên bài |
|---|---:|---|---|
| Hai | 1 | Tiếng Việt | Bài A |
| Hai | 2 | Toán | Bài B |
| Hai | 3 | Khoa học | Bài C |
| Ba | 1 | Toán | Bài D |

**Đích — lớp 5B**

| Thứ | Tiết | Môn | Nội dung sau đồng bộ |
|---|---:|---|---|
| Hai | 1 | Toán | Bài B |
| Hai | 2 | Tiếng Việt | Bài A |
| Hai | 3 | Khoa học | Bài C |
| Ba | 1 | Toán | Bài D |

Bảng trên chỉ minh họa nguyên tắc ghép theo môn, không phải dữ liệu thực tế.

## 4.7. Xử lý số tiết không khớp \[ĐÃ CHỐT\]

Nếu một môn có số bản ghi nguồn khác số slot đích:

- **Bỏ qua môn đó** trong tuần đó; các môn khớp vẫn được xử lý bình thường.
- Không ghi bất kỳ ô nào của môn bị bỏ qua (giữ nguyên nội dung sheet tuần).
- Không tự lấy tiết ở tuần khác để bù.
- Không tự bỏ bản ghi thừa.
- Hiển thị trong preview và màn hình kết quả: tuần, môn, số lượng nguồn, số lượng đích, chênh lệch.
- Giáo viên tự điền các môn bị bỏ qua trên file kết quả.

Ví dụ:

| Môn | Nguồn | Đích | Kết quả |
|---|---:|---:|---|
| Toán | 5 | 5 | Điền |
| Tiếng Việt | 7 | 6 | Bỏ qua — lệch 1 tiết |
| Khoa học | 2 | 2 | Điền |

Lỗi **chặn cả tuần** chỉ gồm lỗi cấu trúc: sheet thiếu, sheet trùng, sheet sai cấu trúc, không đọc được ngày tháng. Lệch số tiết là **cảnh báo theo môn**, không chặn tuần.

## 4.8. Tuần có ngày nghỉ (nghỉ lễ, nghỉ đột xuất) \[ĐÃ CHỐT\]

Nguyên tắc: **thông báo để giáo viên điều chỉnh; chỉ xử lý các môn không bị ảnh hưởng.**

### Tiết nghỉ và buổi nghỉ \[ĐÃ CHỐT\]

Nguyên tắc người dùng xác nhận: **có nội dung thì xử lý, không có nội dung thì không xử lý và cảnh báo.**

1. **Tiết nghỉ** (xét trên file nguồn): ô tên bài (cột E) **trống**, **hoặc** ô môn/tên bài có chữ **"nghỉ"** (không phân biệt hoa/thường, sau chuẩn hóa Unicode).
   - Không phân biệt "quên điền" với "nghỉ thật": cả hai đều là tiết không có nội dung, nên không xử lý.
2. **Buổi nghỉ**: một buổi (sáng/chiều của một ngày) mà **mọi** tiết đều là tiết nghỉ. Ngày nghỉ = cả hai buổi đều nghỉ. Khái niệm này dùng để kiểm tra phía file đích (xem dưới).

Cách file thực tế ghi ngày nghỉ (`LBG_mau.xlsx`, `TUẦN 7`, thứ Năm 22/10): vùng `E23:F28` được **gộp thành một ô và để trống**, cột D vẫn giữ tên môn. Theo quy tắc trên, cả 6 tiết là tiết nghỉ nên cả ngày thứ Năm là ngày nghỉ.

- Vì vậy kiểm tra cấu trúc **file nguồn** phải cho phép **vùng gộp thêm trong cột E:F** (đánh dấu nghỉ). File đích vẫn kiểm tra đúng danh sách vùng gộp chuẩn, vì sheet tuần đích copy từ `MẪU` và chưa có dữ liệu.

Các trường hợp trong file mẫu:

| Trường hợp | Kết quả |
|---|---|
| `HĐTN (SHDC)` (mọi tuần, luôn trống tên bài) | Tiết nghỉ → môn bị bỏ qua, ô đích giữ nguyên (vốn trống); cảnh báo mức thông tin |
| `TUẦN 3`, thứ Sáu tiết 3, `HĐTV` (quên điền) | Tiết nghỉ → HĐTV tuần 3 bị bỏ qua; cảnh báo để giáo viên điền |
| `TUẦN 7`, cả ngày thứ Năm trống | Ngày nghỉ → các môn có tiết thứ Năm ở nguồn hoặc ở đích bị bỏ qua |

Preview cho phép giáo viên tự đánh dấu/bỏ đánh dấu buổi nghỉ nếu hệ thống nhận diện sai.

### Xác định môn bị ảnh hưởng

Một môn **bị ảnh hưởng** nếu:

- có ít nhất một **tiết nghỉ** của môn đó trong file nguồn, hoặc một tiết của môn đó nằm trong **buổi nghỉ** của file nguồn; **hoặc**
- có ít nhất một slot của môn đó trên sheet tuần đích nằm trong **buổi nghỉ**.

Phải xét cả hai phía, vì chỉ so số lượng là không đủ. Ví dụ ngày nghỉ là thứ Hai:

- Nguồn: Khoa học học thứ Ba, thứ Năm → vẫn đủ 2 tiết.
- Đích: Khoa học học thứ Hai, thứ Tư → 2 slot.
- Số lượng khớp, nhưng nếu ghép sẽ điền bài vào thứ Hai là ngày nghỉ → **sai**.

Do đó Khoa học phải bị bỏ qua dù số lượng khớp.

Vì sao bỏ qua **cả môn**, không điền riêng các tiết có nội dung: khi một tiết nguồn bị thiếu, không xác định được các tiết còn lại nên dồn vào slot đích nào. Ghép lệch một tiết sẽ làm sai toàn bộ các tiết sau của môn đó. Bỏ qua cả môn và báo rõ là an toàn hơn.

Kết quả chạy prototype với dữ liệu thật — nguồn `LBG_mau.xlsx`/`TUẦN 7` (thứ Năm nghỉ), đích theo TKB lớp trong `TUẦN 8.xlsx`, chỉ các môn mặc định:

| Môn | Nguồn | Đích | Kết quả |
|---|---:|---:|---|
| Tiếng Việt | 7 | 7 | Bỏ qua — nguồn nghỉ thứ Năm; đích có tiết thứ Năm |
| Toán | 5 | 5 | Bỏ qua — nguồn nghỉ thứ Năm; đích có tiết thứ Năm |
| HĐTN | 1 | 1 | Bỏ qua — nguồn nghỉ thứ Năm; đích có tiết thứ Năm |
| HĐTN (SHDC) | 1 | 1 | Bỏ qua — không có nội dung |
| Khoa học, Đạo đức, HĐTN (SHL), GDTC chung | — | — | Điền |

### Hành động

- Môn bị ảnh hưởng: bỏ qua, ghi cảnh báo `AFFECTED_BY_DAY_OFF` kèm tiết/buổi nghỉ.
- Môn không bị ảnh hưởng: xử lý bình thường theo mục 4.6, 4.7.
- Các ô của buổi nghỉ trên sheet đích: không ghi gì, giáo viên tự điều chỉnh.
- Màn hình kết quả nhắc rõ: "Tuần X có ngày nghỉ [thứ, ngày]. Các môn sau cần điền thủ công: …".

Lưu ý: file mẫu 9 tuần chưa có tuần nghỉ lễ thật. Cần thêm ít nhất một tuần có nghỉ lễ (ghi chữ "Nghỉ" và/hoặc để trống) vào bộ test.

## 4.9. Môn do giáo viên bộ môn dạy \[ĐÃ CHỐT\]

### Chọn môn cần đồng bộ \[ĐÃ CHỐT\]

- Nguyên tắc: **giáo viên tích chọn môn nào thì đồng bộ môn đó**.
- Danh sách môn hiển thị là các môn tìm thấy trong file nguồn và sheet tuần đích đã chọn, sau chuẩn hóa tên. Nhóm hoán đổi (mục 4.10) hiện thành một mục, ví dụ "HĐTV / HĐTT".
- Có nút "Chọn tất cả" / "Bỏ chọn tất cả".
- Lựa chọn được nhớ trong trình duyệt (`localStorage`) cho lần sau.
- Môn không được chọn: hệ thống không đọc, không so sánh, không ghi ô của môn đó.

### Giá trị mặc định: các môn giáo viên bộ môn không được chọn \[ĐÃ CHỐT\]

- Lần đầu sử dụng (chưa có lựa chọn đã lưu), các môn giáo viên bộ môn **không được tích sẵn**. Đó là các môn tô chữ đỏ trong file mẫu: `Âm nhạc`, `Mỹ thuật`, `Tiếng Anh`, `Tin học`, `Công nghệ`, `GDTC`, `Lịch sử & Địa lí`, `HĐTV`/`HĐTT`.
- Các môn còn lại được tích sẵn: `Tiếng Việt`, `Toán`, `Khoa học`, `Đạo đức`, `HĐTN`, `HĐTN (SHDC)`, `HĐTN (SHL)`, `GDTC chung`.
- Danh sách mặc định nằm trong `subject_config.json` → `default_excluded_subjects`. Hệ thống **không** dựa vào màu chữ trong file để quyết định.
- Môn bộ môn vẫn có tên bài trong file. Nếu giáo viên tích chọn thì các môn này được xử lý như môn thường.

## 4.10. Chuẩn hóa tên môn

Cần chuẩn hóa trước khi so sánh:

- Trim khoảng trắng đầu/cuối.
- Gộp nhiều khoảng trắng liên tiếp.
- Chuẩn hóa Unicode về NFC để tránh lỗi khác biệt biểu diễn ký tự.
- So sánh không phân biệt chữ hoa/chữ thường.
- Có bảng alias cấu hình được, ví dụ `LS&ĐL` tương đương `Lịch sử & Địa lí`.

Không tự động gộp các hoạt động có tên gần giống nhau nếu chưa có quy tắc.

Các mục như `GDTC chung`, `HĐTN (SHDC)`, `HĐTN (SHL)`, hoạt động thư viện hoặc tiết sinh hoạt cần được giữ đúng loại. Không được mặc định xem tất cả là một môn.

### Danh sách tên môn trong file mẫu

| Tên trong file | Số tiết/tuần | Ghi chú |
|---|---:|---|
| `Tiếng Việt` | 7 | |
| `Toán` | 5 | |
| `Tiếng Anh` | 4 | Chữ đỏ |
| `Khoa học` | 2 | |
| `GDTC` | 2 | Chữ đỏ |
| `Lịch sử & Địa lí` | 2 | Chữ đỏ |
| `Âm nhạc` | 1 | Chữ đỏ |
| `Mỹ thuật` | 1 | Chữ đỏ (viết "Mỹ", không phải "Mĩ") |
| `Tin học` | 1 | Trong file có dấu cách thừa ở cuối: `"Tin học "` |
| `Công nghệ` | 1 | Chữ đỏ |
| `Đạo đức` | 1 | |
| `HĐTN` | 1 | |
| `HĐTN (SHDC)` | 1 | Luôn không có tên bài → tiết nghỉ, không xử lý, cảnh báo mức thông tin |
| `HĐTN (SHL)` | 1 | |
| `GDTC chung` | 1 | Chữ đậm; tên bài cố định "Sinh hoạt chung toàn trường" |
| `HĐTV` | 1 | Tuần lẻ (1, 3, 5, 7, 9), thứ Sáu tiết 3 |
| `HĐTT` | 1 | Tuần chẵn (2, 4, 6, 8), cùng vị trí với HĐTV |

Tổng 32 tiết/tuần.

### Nhóm hoán đổi HĐTV / HĐTT \[ĐÃ CHỐT — phương án b\]

`HĐTV` và `HĐTT` thay phiên nhau theo tuần ở cùng một tiết. Sheet `MẪU` ghi `HĐTV`, nên tuần chẵn copy từ `MẪU` sẽ ghi sai tên. Cách xử lý:

- Khai báo trong `subject_config.json` → `interchangeable_groups: [["HĐTV", "HĐTT", "HĐTV/HĐTT"]]`. Trong file đích mẫu `TUẦN 8.xlsx`, giáo viên ghi ô môn là `HĐTV/HĐTT`; tên này cũng thuộc nhóm.
- Khi gom và đếm, mọi môn thuộc nhóm được coi là **một môn** (khóa nhóm `HĐTV/HĐTT`). Áp dụng đủ các quy tắc thứ tự, số lượng (mục 4.7) và nghỉ (mục 4.8).
- Khi ghép bản ghi nguồn vào slot đích, hệ thống ghi tên bài, đồ dùng **và ghi luôn ô môn (cột D) theo tên môn của nguồn**. Ví dụ tuần 8 (đã chạy prototype): nguồn là `HĐTT`, slot đích đang ghi `HĐTV/HĐTT` → ô D được ghi thành `HĐTT`.
- Đây là **ngoại lệ duy nhất** hệ thống được ghi cột D. Chỉ thay giá trị chữ, giữ nguyên style (màu chữ đỏ của ô đích).
- Preview hiển thị rõ "Đổi tên môn: HĐTV → HĐTT" tại slot đó.
- Nhóm này thuộc nhóm môn bộ môn, nên mặc định không được tích chọn (mục 4.9). Quy tắc chỉ chạy khi giáo viên tích chọn "HĐTV / HĐTT".

Tên môn chỉ có ở một phía (nguồn có mà đích không có, hoặc ngược lại) → cảnh báo `UNKNOWN_SUBJECT`, bỏ qua môn đó. **\[ĐỀ XUẤT\]** Preview cho phép giáo viên ghép tạm hai tên môn với nhau trong lượt xử lý hiện tại.

## 4.11. Ngày tháng và tiêu đề tuần

Kết quả phân tích file mẫu: mọi ô ngày tháng là **chuỗi văn bản**, không phải kiểu ngày và không phải công thức.

| Ô | Nội dung mẫu | Ghi chú |
|---|---|---|
| `A1` (gộp `A1:F1`) | `" TUẦN 01 (Từ 07/09/2026 đến 11/09/2026)"` | Có dấu cách đầu; số tuần 2 chữ số |
| `A3`, `A10`, `A17`, `A23`, `A29` | `"Hai (07/09)"`, `"Ba (08/09)"`, `"Tư (09/09)"`, `"Năm (10/09)"`, `"Sáu (11/09)"` | Ô gộp theo ngày |
| `E35` (gộp `E35:F35`) | `"                                         Ngày 04 tháng 9 năm 2026"` | Ngày ký, là thứ Sáu tuần trước; căn lề bằng dấu cách |

Quy tắc:

- Copy **nguyên văn** chuỗi từ các ô trên của file nguồn sang sheet đích, kể cả dấu cách đầu dòng. Không tự dựng lại chuỗi, vì hai lớp cùng trường dùng chung lịch.
- Trước khi copy, parse để kiểm tra: số tuần trong `A1` khớp tên sheet; ngày trong `A3…A29` nằm trong khoảng ngày của `A1`; `E35` đúng mẫu "Ngày d tháng m năm yyyy". Không khớp → lỗi chặn tuần `INVALID_SOURCE_DATE`.
- `E36` ("BGH duyệt") và hàng tiêu đề `A2:F2` là nội dung cố định, không ghi.
- Không thay đổi ô nào ngoài các ô đã khai báo.

## 4.12. Ô trống \[ĐÃ CHỐT\]

- Nếu bản ghi nguồn có tên bài trống → ô tên bài đích **để trống**.
- Nếu bản ghi nguồn có đồ dùng trống → ô đồ dùng đích **để trống**, kể cả khi sheet `MẪU` có nội dung mặc định ở ô đó.
- Quy tắc này chỉ áp dụng cho các môn được xử lý. Môn bị bỏ qua (mục 4.7, 4.8, 4.9) thì giữ nguyên nội dung sheet tuần.
- Tiết có tên bài trống ở nguồn là **tiết nghỉ** (mục 4.8): môn đó không được xử lý trong tuần, giữ nguyên ô đích, và có cảnh báo `EMPTY_LESSON` để giáo viên kiểm tra/điền bổ sung.
- Với tiết **có** tên bài nhưng đồ dùng trống: vẫn xử lý; ô đồ dùng đích để trống.

------------------------------------------------------------------------

# 5. Bảo toàn định dạng Excel

## 5.1. Nguyên tắc

- Sheet tuần do giáo viên tạo bằng Excel, nên định dạng ban đầu là chuẩn.
- Hệ thống chỉ thay **giá trị** của các ô được khai báo trong template profile, bằng cách sửa trực tiếp XML (mục 5.3).
- Không đổi style index của ô, kích thước dòng/cột, merged cells hay bất kỳ phần nào khác của file.
- Không sao chép style từ file nguồn.
- Không thay đổi sheet `MẪU`.
- Không tạo, xóa hoặc đổi tên sheet.

## 5.2. Không tự điều chỉnh format

Không tự động đổi font, cỡ chữ, màu, border, chiều cao dòng, chiều rộng cột, merged cells, layout trang in.

Nếu nội dung dài có nguy cơ bị cắt, hệ thống hiển thị cảnh báo. Không tự thay đổi chiều cao dòng.

## 5.3. Kết quả test round-trip (Phase 0) và quyết định writer

**Thành phần của file mẫu:** không có công thức, ảnh, shape, data validation, conditional formatting, named range hay freeze panes. Page setup: giấy Letter (`paperSize=1`), dọc, lề mặc định. File được lưu bởi Excel và có dấu vết WPS Office (custom properties `KSOProductBuildVer`).

**Thử nghiệm 1 — openpyxl load → ghi `TUẦN 9` → save:**

- Giá trị các sheet không ghi: không đổi.
- So sánh bằng chính openpyxl: không thấy khác biệt. Lý do là openpyxl đã "chuẩn hóa" style ngay khi load, nên phép so sánh này **không phát hiện được lỗi**.
- So sánh XML và ảnh render (LibreOffice → PDF → pixel) thì **có khác biệt ở cả các sheet không ghi**:
  - Style của các ô bên trong vùng gộp (ví dụ cột Buổi `B3:B6`) bị viết lại: đường chéo vẽ trong từng ô bị thay bằng border của vùng gộp.
  - Mọi dòng bị gắn `customHeight="1"`. Các dòng vốn tự giãn chiều cao trở thành cố định, nên bố cục in thay đổi.
  - Mất một số phần mở rộng: `x14:slicerStyles`, `xcalcf:calcFeatures`, namespace WPS. Ảnh hưởng không đáng kể.
  - Shared strings chuyển thành inline strings. File vẫn hợp lệ.

**Thử nghiệm 2 — sửa trực tiếp XML** (giải nén gói `.xlsx`, dùng `lxml` sửa đúng các phần tử `<c>` cần ghi, giữ nguyên thuộc tính `s` là style, nén lại):

- Các sheet không ghi: render PDF **giống từng pixel** với file gốc.
- Sheet được ghi: giữ nguyên định dạng; chỉ nội dung các ô đã ghi thay đổi.
- Đọc lại bằng openpyxl cho đúng giá trị.

**Quyết định \[ĐỀ XUẤT mạnh\]:**

- **Đọc** workbook bằng openpyxl (chỉ đọc giá trị).
- **Ghi** bằng cách sửa trực tiếp XML của sheet. Ghi chuỗi dạng `inlineStr`; xóa giá trị bằng cách bỏ `<v>`/`<is>` và thuộc tính `t`; luôn giữ nguyên thuộc tính `s`.
- Ô cần ghi bắt buộc đã tồn tại trong XML (bố cục cố định). Không có thì báo `INVALID_SHEET_STRUCTURE`, không tự tạo ô.
- Các file khác trong gói (styles, sharedStrings, workbook, docProps…) được copy nguyên byte.
- Nếu gói có `xl/calcChain.xml` (file có công thức) thì giữ nguyên, vì hệ thống không đụng ô công thức.

Prototype đã chạy thử nằm ở bước Phase 0. Writer chính thức viết lại trong `workbook_writer.py`.

## 5.4. Kiểm tra định dạng tự động

Viết test so sánh trước/sau cho mỗi sheet:

- **Mức gói:** mọi part trong file `.xlsx` ngoài các sheet được ghi phải giống nguyên byte với file đích gốc.
- **Mức XML của sheet được ghi:** so sánh cây XML trước/sau; khác biệt chỉ được phép nằm ở nội dung (`<v>`, `<is>`, thuộc tính `t`) của các ô trong whitelist. Thuộc tính `s` (style), `<row>`, `<cols>`, `<mergeCells>`, `<pageSetup>`… phải giữ nguyên.
- **Mức hiển thị (test tích hợp):** render bằng LibreOffice headless ra PDF; các trang của sheet không ghi phải giống từng pixel.

Không dùng openpyxl để so sánh style trước/sau, vì openpyxl chuẩn hóa style khi load và che mất khác biệt (đã kiểm chứng ở Phase 0).

------------------------------------------------------------------------

# 6. Kiến trúc hạ tầng

## 6.1. Lựa chọn kiến trúc MVP \[ĐÃ CHỐT — v1.5\]

**Một ứng dụng Laravel duy nhất** phục vụ cả giao diện lẫn API:

- Giao diện: Vue 3 SPA (vue-router, pinia) trong `resources/js`, build bằng Vite qua `laravel-vite-plugin`.
- Laravel trả về một view `app.blade.php` cho mọi đường dẫn không bắt đầu bằng `/api`; vue-router xử lý điều hướng phía trình duyệt.
- API: Laravel, prefix `/api/v1`, **cùng origin** với giao diện.
- Python: script nội bộ được Laravel gọi bằng Symfony Process.
- Deploy: một Docker Web Service trên Render Free (Nginx + PHP-FPM + Python + asset Vue đã build).
- Database: chưa dùng ở MVP.
- File storage lâu dài: chưa dùng ở MVP.
- File tạm: filesystem của container, chỉ dùng trong vòng đời xử lý.
- Source code: repo GitHub `teacher-workspace`.

Lý do gộp giao diện vào Laravel thay vì tách lên Cloudflare Pages (phương án của bản 1.0–1.4):

- Không cần proxy trung gian. Upload multipart, download file nhị phân, cookie, CSRF đều chạy trực tiếp cùng origin; đây là phần rủi ro nhất của phương án tách.
- Session cookie của Laravel hoạt động ngay, không có vấn đề CORS hay cookie khác site.
- Một nơi deploy, một domain, một bộ biến môi trường.
- Dễ chuyển sang VPS sau này.

Đánh đổi chấp nhận: khi Render đang ngủ, lần mở trang đầu tiên phải chờ cold start (trang trắng tới khoảng 1 phút). Với phương án tách, giao diện hiện ngay nhưng vẫn phải chờ ngần ấy mới gọi được API, nên khác biệt thực tế nhỏ với một người dùng.

Lý do không tách Python thành service riêng:

- Chỉ có một người dùng.
- Tác vụ Excel hiện tại ngắn.
- Không cần giao tiếp HTTP giữa Laravel và Python.
- Giảm số dịch vụ cần deploy, theo dõi và cold start.
- Có thể tách Python thành service riêng khi tải tăng.

**Phương án thay thế \[ĐỀ XUẤT xem xét\]:** một VPS nhỏ (khoảng 100–150 nghìn đồng/tháng) chạy cùng image Docker. Ưu điểm: không cold start, filesystem bền, có sẵn chỗ cho PostgreSQL ở giai đoạn 2. Nhược điểm: tự vận hành, tự backup.

## 6.2. Sơ đồ request

```text
Browser
  |
  | HTTPS (một domain)
  v
Render Docker Web Service
  |
  +--> Nginx
  |      +--> /build/*  : asset Vue đã build (file tĩnh)
  |      +--> còn lại   : PHP-FPM
  |
  +--> PHP-FPM / Laravel
          |
          +--> GET /{bất kỳ, trừ /api}  -> app.blade.php (Vue SPA)
          |
          +--> /api/v1/*
                  +--> Validate request, auth
                  +--> Store temporary uploads + meta.json
                  +--> Symfony Process
                  |       |
                  |       v
                  |     Python
                  |       +--> Read source workbook (openpyxl)
                  |       +--> Read target workbook (existing week sheets)
                  |       +--> Detect days off, filter subjects
                  |       +--> Validate week/subject counts
                  |       +--> Patch sheet XML of target (lxml)
                  |       +--> Save result workbook (new file)
                  |
                  +--> Return preview / download
                  +--> Cleanup temporary files
```

## 6.3. Chạy local

- `php artisan serve` (cổng 8000) phục vụ cả giao diện và API.
- `npm run dev` chạy Vite dev server; `@vite` trong blade tự nạp code từ Vite (hot reload). Không cần proxy.
- Khi không chạy `npm run dev`, Laravel dùng bản build trong `public/build` (`npm run build`).

## 6.4. Giới hạn gói miễn phí

Các gói miễn phí có thể thay đổi theo thời gian. Trước khi deploy phải kiểm tra lại pricing/limits chính thức.

Rủi ro đã biết của Render Free:

- Web service ngủ sau khoảng 15 phút không có request; request đầu tiên sau đó phải chờ cold start (có thể tới khoảng 1 phút), **kể cả việc tải giao diện**.
- Khi ngủ hoặc redeploy, **toàn bộ file tạm bị mất**.
- RAM (khoảng 512MB) và CPU giới hạn.
- Không phù hợp với dịch vụ cần uptime production được đảm bảo.

Do đó:

- Không lưu dữ liệu lâu dài trong container.
- Giao diện phải xử lý êm trường hợp job bị mất (`JOB_NOT_FOUND` → "Phiên xử lý đã hết hạn, vui lòng upload lại").
- Không chạy tác vụ nặng kéo dài trên request HTTP.
- Giới hạn dung lượng file upload và thời gian xử lý.
- Nếu cần độ ổn định cao, chuyển sang Render paid hoặc VPS.

## 6.5. Không dùng database trong MVP

Chức năng hiện tại chạy stateless theo job:

1. Upload file.
2. Xử lý.
3. Trả kết quả.
4. Xóa file tạm.

Trạng thái job lưu trong `meta.json` của thư mục job (mục 11.1). Đăng nhập không cần database (mục 12.1).

------------------------------------------------------------------------

# 7. Cấu trúc repository

Laravel nằm ở **thư mục gốc** của repo (cấu trúc Laravel chuẩn), giao diện Vue trong `resources/js`, Python trong `python/`.

```text
teacher-workspace/
├── app/
│   ├── Auth/                           # Custom user provider từ env (Phase 3)
│   ├── Http/
│   │   ├── Controllers/Api/
│   │   ├── Requests/
│   │   └── Resources/
│   ├── Services/
│   │   └── Timetable/
│   └── Exceptions/
├── bootstrap/
├── config/
│   └── timetable.php
├── public/
│   └── build/                          # Asset Vue đã build (không commit)
├── resources/
│   ├── css/app.css
│   ├── js/                             # Vue SPA
│   │   ├── app.js
│   │   ├── App.vue
│   │   ├── layouts/
│   │   ├── pages/
│   │   │   ├── LoginPage.vue
│   │   │   ├── DashboardPage.vue
│   │   │   └── TimetableSyncPage.vue
│   │   ├── router/
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── timetable.js
│   │   └── stores/
│   └── views/app.blade.php             # Khung SPA
├── routes/
│   ├── api.php                         # /api/v1/*
│   └── web.php                         # Mọi đường dẫn khác -> SPA
├── storage/
│   └── app/private/timetable-jobs/     # File tạm của job (không commit)
├── python/
│   ├── process_timetable.py            # CLI entrypoint
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── config/
│   │   ├── template_profile.json       # Tọa độ ô, cấu trúc sheet
│   │   └── subject_config.json         # Alias, nhóm hoán đổi, môn mặc định
│   ├── common/
│   │   ├── config.py
│   │   ├── normalization.py
│   │   ├── workbook_reader.py
│   │   ├── timetable_parser.py
│   │   ├── day_off_detector.py
│   │   ├── timetable_matcher.py
│   │   ├── workbook_writer.py
│   │   └── validators.py
│   └── tests/
│       └── fixtures/                   # Workbook mẫu của giáo viên
├── tests/                              # Test Laravel
├── docker/
│   ├── nginx.conf.template
│   ├── php.ini
│   ├── php-fpm.conf
│   ├── supervisord.conf
│   └── entrypoint.sh
├── Dockerfile
├── .dockerignore
├── render.yaml                         # Render Blueprint
├── docs/
│   ├── DETAIL_DESIGN.md
│   ├── deployment.md
│   ├── user-guide.md                   # Hướng dẫn giáo viên chuẩn bị file
│   └── phase0/                         # Prototype và kết quả Phase 0
├── composer.json
├── package.json
├── vite.config.js
├── .env.example
├── CLAUDE.md                           # Quy tắc cho Claude Code (từ mục 22)
├── .gitignore
└── README.md
```

Không bắt buộc phải tạo mọi file/thư mục ngay lập tức. Developer có thể tạo dần theo từng phase.

## 7.1. Nguyên tắc phân lớp backend

**Controller:**

- Nhận HTTP request.
- Validate dữ liệu.
- Gọi service.
- Trả response.

**Service:**

- Điều phối nghiệp vụ.
- Tạo thư mục job và `meta.json`.
- Gọi Python.
- Đọc kết quả JSON.
- Quản lý cleanup.

**Python:**

- Parse workbook.
- Chuẩn hóa môn.
- Nhận diện ngày nghỉ.
- Match nội dung, kiểm tra số lượng.
- Ghi giá trị vào workbook kết quả.
- Không xử lý authentication hoặc HTTP.

Không nhồi toàn bộ logic Excel vào controller.

------------------------------------------------------------------------

# 8. Thiết kế chi tiết module Excel

## 8.1. Các thành phần

### `workbook_reader.py`

- Mở workbook bằng openpyxl chỉ để **đọc** (cả nguồn và đích; cần đọc merged ranges nên không dùng `read_only`).
- Liệt kê sheet.
- Nhận diện sheet tuần và số tuần.
- Xử lý lỗi file hỏng hoặc sai định dạng.

### `timetable_parser.py`

- Đọc sheet theo template profile.
- Nhận diện ngày/thứ, ngày tháng, buổi, tiết, môn.
- Đọc tên bài và đồ dùng.
- Xác định tọa độ ô.
- Xử lý merged cells.

### `normalization.py`

- Trim, gộp khoảng trắng, Unicode NFC, hoa/thường.
- Áp dụng alias môn.
- Chuẩn hóa tên sheet tuần → số tuần.

### `day_off_detector.py`

- Nhận diện ngày nghỉ trong tuần nguồn (mục 4.8).
- Nhận danh sách ngày nghỉ do giáo viên chỉnh tay (nếu có).
- Xác định môn bị ảnh hưởng ở cả nguồn và đích.

### `timetable_matcher.py`

- Lọc môn không đồng bộ.
- Gom lesson records và target slots theo môn, giữ thứ tự.
- So sánh số lượng.
- Tạo mapping nguồn → đích cho các môn hợp lệ.
- Sinh cảnh báo/lỗi có cấu trúc.

### `workbook_writer.py`

- **Không dùng openpyxl để ghi** (mục 5.3).
- Mở gói `.xlsx` đích bằng `zipfile`; ánh xạ tên sheet → part XML qua `xl/workbook.xml` và `xl/_rels/workbook.xml.rels`.
- Với mỗi tuần `ready`: dùng `lxml` sửa các ô tiêu đề tuần, ngày, ngày ký, tên bài, đồ dùng theo mapping.
- Giữ nguyên thuộc tính style `s`; không tạo ô mới; không tạo/xóa sheet.
- Ghi gói mới: part không đổi thì copy nguyên byte, giữ thứ tự và metadata của các entry trong zip.

### `validators.py`

- Kiểm tra workbook mở được, có sheet `MẪU`.
- Kiểm tra cấu trúc sheet tuần khớp template profile.
- Kiểm tra trạng thái sheet tuần (`ready`/`has_data`/…).
- Kiểm tra sau khi ghi: chỉ các ô trong whitelist thay đổi; style và merged ranges không đổi; output mở lại được.

## 8.2. Template profile

Mọi tọa độ ô và quy tắc cấu trúc nằm trong `template_profile.json`, không hardcode trong parser. **\[ĐÃ CHỐT\]** Tọa độ cố định, lấy từ file mẫu `LBG_mau.xlsx`:

Bố cục sheet (vùng `A1:F36`):

| Ngày | Ô ngày (gộp) | Buổi sáng | Buổi chiều | Số tiết |
|---|---|---|---|---:|
| Hai | `A3:A9` | dòng 3–6 (`B3:B6`) | dòng 7–9 (`B7:B9`) | 7 |
| Ba | `A10:A16` | dòng 10–13 (`B10:B13`) | dòng 14–16 (`B14:B16`) | 7 |
| Tư | `A17:A22` | dòng 17–20 (`B17:B20`) | dòng 21–22 (`B21:B22`) | 6 |
| Năm | `A23:A28` | dòng 23–26 (`B23:B26`) | dòng 27–28 (`B27:B28`) | 6 |
| Sáu | `A29:A34` | dòng 29–32 (`B29:B32`) | dòng 33–34 (`B33:B34`) | 6 |

Cột: `C` = số tiết, `D` = môn, `E` = tên bài, `F` = đồ dùng dạy học.

Ghi chú: giá trị cột `C` (số thứ tự tiết) **khác nhau giữa các sheet**, ví dụ chiều thứ Tư là 6–7 ở `MẪU` và `TUẦN 9` nhưng là 5–6 ở `TUẦN 1`. Vì vậy hệ thống xác định slot theo **dòng**, không theo số tiết, và không ghi cột `C`.

```json
{
  "profile_id": "lbg-tieu-hoc-v1",
  "template_sheet": "MẪU",
  "week_sheet_pattern": "^TU[ẦA]N\\s*0*(\\d{1,2})$",
  "used_range": "A1:F36",
  "cells": {
    "week_title": "A1",
    "sign_date": "E35"
  },
  "structure_anchors": [
    { "cell": "A2", "value": "Thứ" },
    { "cell": "B2", "value": "Buổi" },
    { "cell": "C2", "value": "Tiết" },
    { "cell": "D2", "value": "Môn" },
    { "cell": "E2", "value": "Tên bài" }
  ],
  "expected_merged_ranges": [
    "A1:F1", "A3:A9", "A10:A16", "A17:A22", "A23:A28", "A29:A34",
    "B3:B6", "B7:B9", "B10:B13", "B14:B16", "B17:B20", "B21:B22",
    "B23:B26", "B27:B28", "B29:B32", "B33:B34", "E35:F35", "E36:F36"
  ],
  "days": [
    { "label": "Hai", "date_cell": "A3",  "sessions": { "SÁNG": [3, 6],   "CHIỀU": [7, 9] } },
    { "label": "Ba",  "date_cell": "A10", "sessions": { "SÁNG": [10, 13], "CHIỀU": [14, 16] } },
    { "label": "Tư",  "date_cell": "A17", "sessions": { "SÁNG": [17, 20], "CHIỀU": [21, 22] } },
    { "label": "Năm", "date_cell": "A23", "sessions": { "SÁNG": [23, 26], "CHIỀU": [27, 28] } },
    { "label": "Sáu", "date_cell": "A29", "sessions": { "SÁNG": [29, 32], "CHIỀU": [33, 34] } }
  ],
  "columns": {
    "period": "C",
    "subject": "D",
    "lesson": "E",
    "equipment": "F"
  }
}
```

- Không dùng `E35`/`E36` (ngày ký, "BGH duyệt") làm mốc cấu trúc: file đích thật `TUẦN 8.xlsx` để trống hai ô này (ô vẫn tồn tại và có định dạng, nên vẫn ghi được ngày ký).
- `structure_anchors` và `expected_merged_ranges` dùng để kiểm tra sheet tuần có đúng cấu trúc (trạng thái `invalid_structure`). Không kiểm tra ô môn học, vì giáo viên được phép sửa TKB từng tuần.
- Ô cho phép ghi (whitelist): `A1`, `A3`, `A10`, `A17`, `A23`, `A29`, `E35`, `E3:E34`, `F3:F34`; cột `D` chỉ khi áp dụng nhóm hoán đổi (mục 4.10).
- Khi mở rộng sang trường/khối khác chỉ cần thêm profile mới.

## 8.3. Hợp đồng Laravel ↔ Python

CLI:

```text
python3 process_timetable.py <command> --job-dir <path> [--request <path/to/request.json>]
command: list-weeks | analyze | generate
```

Quy ước:

- **Input:** `request.json` trong thư mục job (tuần chọn, môn đồng bộ, ngày nghỉ chỉnh tay).
- **Output:** ghi kết quả ra `weeks.json` / `analysis.json` / `generate.json` trong thư mục job. stdout không dùng cho kết quả.
- **Log:** chỉ ghi ra stderr, dạng JSON line.
- **Exit code:** `0` thành công; `1` lỗi nghiệp vụ (đã ghi `error` trong file kết quả); `2` lỗi hệ thống/không xác định.
- Laravel đặt timeout cho Process **\[ĐỀ XUẤT: 60 giây\]**.

## 8.4. Data contract `analysis.json`

Schema minh họa (cần định nghĩa schema chính thức và validate ở cả hai phía):

```json
{
  "success": true,
  "source_sha256": "...",
  "target_sha256": "...",
  "request": {
    "weeks": [7, 8],
    "selected_subjects": ["Khoa học", "Toán", "Tiếng Việt", "HĐTV/HĐTT"],
    "manual_days_off": []
  },
  "can_generate": true,
  "weeks": [
    {
      "week_number": 7,
      "source_sheet": "TUẦN 7",
      "target_sheet": "TUẦN 7",
      "target_status": "ready",
      "selectable": true,
      "status": "ready",
      "errors": [],
      "days_off": [
        { "day": "Năm", "session": "SÁNG", "detected_by": "auto" },
        { "day": "Năm", "session": "CHIỀU", "detected_by": "auto" }
      ],
      "subjects": [
        {
          "subject": "Khoa học",
          "source_count": 2,
          "target_count": 2,
          "status": "matched",
          "items": [
            {
              "order": 1,
              "source_ref": "TUẦN 7!E8",
              "target_day": "Hai",
              "target_session": "CHIỀU",
              "target_period": "7",
              "lesson": "Vai trò của năng lượng (Tiết 1)",
              "equipment": "Phấn màu",
              "target_lesson_cell": "E9",
              "target_equipment_cell": "F9"
            }
          ]
        },
        {
          "subject": "Toán",
          "source_count": 5,
          "target_count": 5,
          "status": "skipped_day_off",
          "items": []
        }
      ],
      "warnings": [
        { "code": "AFFECTED_BY_DAY_OFF", "message": "Tuần 7, môn Toán: nguồn nghỉ Năm tiết 3; đích có tiết vào buổi nghỉ (Năm tiết 2) — cần điền thủ công.", "details": {} }
      ],
      "writes": { "A1": " TUẦN 07 (Từ 19/10/2026 đến 23/10/2026)", "E9": "Vai trò của năng lượng (Tiết 1)", "F9": "Phấn màu" }
    }
  ]
}
```

- `subject.status`: `matched`, `skipped_count_mismatch`, `skipped_day_off`, `skipped_empty_lesson`, `skipped_unknown_subject`. Môn không được giáo viên chọn không xuất hiện trong `subjects`.
- `target_status`: `ready`, `has_data`, `missing`, `invalid_structure`, `duplicate`. `selectable = true` khi `target_status = ready` và không có lỗi.
- `status` của tuần: `ready` (đã phân tích) hoặc `blocked` (có lỗi chặn tuần trong `errors`).
- `writes`: danh sách ô → giá trị mà `generate` sẽ ghi (nội bộ, frontend không cần hiển thị). Chỉ có khi tuần có ít nhất một môn `matched`; gồm cả các ô tiêu đề/ngày/ngày ký copy từ nguồn.
- Thứ tự ưu tiên khi một môn có nhiều lý do bỏ qua: chỉ có ở một phía → ảnh hưởng ngày nghỉ → tiết trống → lệch số tiết.
- `can_generate = true` khi có ít nhất một tuần `ready` có `writes`.

## 8.5. Đọc sheet tuần

- Tên sheet có số tuần một hoặc hai chữ số, ví dụ `TUẦN 1`, `TUẦN 09`.
- Chuẩn hóa Unicode trước khi so khớp (tên sheet có thể chứa `Ầ` ở dạng tổ hợp).
- Không giả định sheet luôn nằm ở vị trí cố định.
- Bỏ qua sheet không khớp `week_sheet_pattern` (ví dụ `MẪU`, sheet ghi chú).

## 8.6. Thứ tự ghép

Thứ tự lesson nguồn:

- Theo thứ tự ngày rồi theo thứ tự dòng từ trên xuống trong sheet nguồn.
- Nếu workbook có nhiều vùng/buổi, giữ thứ tự xuất hiện theo cấu trúc bảng.

Thứ tự target slot:

- Theo thứ tự dòng từ trên xuống trong sheet đích.
- Không sắp xếp theo tên ngày dạng chữ hoặc theo tên môn.
- Không dùng thứ tự dictionary không xác định.

Sau đó ghép `source_lessons[i]` vào `target_slots[i]` của cùng môn.

## 8.7. Cấu trúc bản ghi

Lesson record (nguồn):

```text
week, day, date, session, period,
subject_raw, subject_normalized,
lesson_name, teaching_equipment,
source_sheet, source_row
```

Target slot (đích):

```text
week, day, date_cell, session, period,
subject_raw, subject_normalized,
lesson_cell, equipment_cell,
target_sheet, target_row, slot_type
```

Không chỉ lưu tên bài; đồ dùng phải gắn cùng record để tránh ghép nhầm.

## 8.8. Cấu hình môn — `subject_config.json`

Không tự động phân loại bằng AI. Bản đầu tiên, theo tên thực tế trong file mẫu \[ĐÃ CHỐT\]:

```json
{
  "subjects": [
    "Tiếng Việt", "Toán", "Tiếng Anh", "Khoa học", "GDTC",
    "Lịch sử & Địa lí", "Âm nhạc", "Mỹ thuật", "Tin học", "Công nghệ",
    "Đạo đức", "HĐTN", "HĐTN (SHDC)", "HĐTN (SHL)", "GDTC chung",
    "HĐTV", "HĐTT"
  ],
  "subject_aliases": {
    "Mĩ thuật": "Mỹ thuật",
    "LS&ĐL": "Lịch sử & Địa lí"
  },
  "default_excluded_subjects": [
    "Tiếng Anh", "Tin học", "Âm nhạc", "Mỹ thuật",
    "Công nghệ", "GDTC", "Lịch sử & Địa lí", "HĐTV/HĐTT"
  ],
  "interchangeable_groups": [
    { "key": "HĐTV/HĐTT", "members": ["HĐTV", "HĐTT", "HĐTV/HĐTT"] }
  ],
  "day_off_keywords": ["nghỉ"]
}
```

- `GDTC` và `GDTC chung` là **hai môn khác nhau**, không gộp.
- `HĐTN`, `HĐTN (SHDC)`, `HĐTN (SHL)` là **ba loại khác nhau**, không gộp.

## 8.9. Preview

Preview hiển thị:

- Tuần, trạng thái sheet tuần đích.
- Ngày nghỉ phát hiện được (cho phép chỉnh).
- Môn, số tiết nguồn, số slot đích, trạng thái (Điền / Bỏ qua + lý do).
- Danh sách nội dung sẽ điền: ngày/tiết đích, tên bài, đồ dùng.
- Cảnh báo tên bài trống hoặc nội dung quá dài.

Không cần hiển thị toàn bộ workbook trong browser. Chỉ cần bảng mapping rõ ràng.

## 8.10. Analyze và Generate

**Analyze/Preview:**

- Chỉ đọc hai file.
- Không tạo workbook kết quả.
- Ghi `analysis.json`.
- Trả mapping dự kiến, cảnh báo và lỗi.

**Generate:**

- Chỉ chạy khi `can_generate = true` và người dùng xác nhận.
- Kiểm tra request generate trùng với request trong `analysis.json` và hash file chưa đổi; nếu khác → yêu cầu analyze lại.
- Load workbook đích, ghi giá trị theo mapping trong `analysis.json`.
- Validate output.
- Lưu `result.xlsx`.

------------------------------------------------------------------------

# 9. Thiết kế API Laravel

Prefix đề xuất: `/api/v1`.

## 9.1. Endpoint

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/auth/login` | Đăng nhập |
| POST | `/auth/logout` | Đăng xuất |
| GET | `/auth/me` | Lấy người dùng hiện tại |
| POST | `/timetable/jobs` | Tạo job, upload hai file, trả luôn danh sách tuần |
| GET | `/timetable/jobs/{job}` | Lấy thông tin/trạng thái job |
| POST | `/timetable/jobs/{job}/analyze` | Phân tích và preview |
| POST | `/timetable/jobs/{job}/generate` | Tạo file kết quả |
| GET | `/timetable/jobs/{job}/download` | Tải file kết quả |
| DELETE | `/timetable/jobs/{job}` | Xóa job và file tạm |
| GET | `/health` | Health check (không cần auth) |

Các endpoint này là đề xuất. Có thể điều chỉnh khi code, nhưng nên giữ ranh giới nghiệp vụ tương tự.

## 9.2. Upload

`POST /api/v1/timetable/jobs` — `multipart/form-data`

```text
source_file: file .xlsx
target_file: file .xlsx
```

Response:

```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "source_file_name": "source.xlsx",
    "target_file_name": "target.xlsx",
    "status": "uploaded",
    "weeks": [
      { "week_number": 7, "source_sheet": "TUẦN 7", "target_sheet": null, "target_status": "missing", "selectable": false, "errors": [{ "code": "TARGET_WEEK_SHEET_MISSING", "message": "Chưa có sheet tuần 7 trong file đích — hãy copy sheet MẪU." }] },
      { "week_number": 8, "source_sheet": "TUẦN 8", "target_sheet": "TUẦN 8", "target_status": "ready", "selectable": true, "errors": [] }
    ],
    "subjects": ["Tiếng Việt", "Toán", "Tiếng Anh", "Khoa học", "HĐTV/HĐTT"],
    "default_selected_subjects": ["Tiếng Việt", "Toán", "Khoa học"],
    "days": [{ "label": "Hai", "sessions": ["SÁNG", "CHIỀU"] }, "…"]
  }
}
```

Validation:

- Có đủ hai file.
- Extension `.xlsx`, MIME/content hợp lệ (file ZIP có `[Content_Types].xml`).
- Kích thước mỗi file trong giới hạn cấu hình **\[ĐỀ XUẤT: 5MB\]**.
- Không tin tên file client gửi lên; tên file gốc chỉ dùng để hiển thị và đặt tên file tải về.
- Lưu bằng tên cố định trong thư mục job UUID.
- Không lưu file trong public directory.

Danh sách tuần lấy từ file nguồn, kèm trạng thái sheet tương ứng ở file đích.

## 9.3. Analyze

`POST /api/v1/timetable/jobs/{job}/analyze`

```json
{
  "weeks": [7, 8],
  "selected_subjects": ["Tiếng Việt", "Toán", "Khoa học"],
  "manual_days_off": [
    { "week_number": 7, "day": "Năm", "is_day_off": true },
    { "week_number": 8, "day": "Hai", "session": "CHIỀU", "is_day_off": false }
  ]
}
```

Laravel ghi request này vào `request.json` của job (mục 8.3). `selected_subjects` là các môn giáo viên tích chọn (mục 4.9); `session` trong `manual_days_off` bỏ trống = cả ngày.

Response: nội dung `analysis.json` (mục 8.4), bỏ trường `writes`.

## 9.4. Generate

`POST /api/v1/timetable/jobs/{job}/generate`

Request: giống analyze. Backend so sánh với `analysis.json`; nếu khác → `ANALYSIS_OUTDATED`.

Response:

- Trạng thái.
- Tên file kết quả.
- Tóm tắt: số tuần đã điền, danh sách môn/tuần bị bỏ qua cần điền thủ công.

## 9.5. Download

`GET /api/v1/timetable/jobs/{job}/download`

- Phải xác thực.
- Kiểm tra job thuộc người dùng hiện tại (`owner` trong `meta.json`).
- Kiểm tra output tồn tại và chưa hết hạn.
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- `Content-Disposition: attachment`, tên file gợi ý dạng `<tên file đích>_dongbo_<yyyymmdd-hhmm>.xlsx` (encode UTF-8 theo RFC 5987).
- Không nhận đường dẫn file tùy ý từ client.

## 9.6. Format lỗi API

```json
{
  "success": false,
  "error": {
    "code": "TEMPLATE_SHEET_MISSING",
    "message": "Không tìm thấy sheet MẪU trong file đích.",
    "details": {}
  }
}
```

Không trả stack trace, đường dẫn nội bộ, secret hoặc thông tin server trong response production.

## 9.7. Danh mục mã lỗi và cảnh báo

| Mã | Loại | Phạm vi | Thông báo mẫu |
|---|---|---|---|
| `INVALID_FILE_TYPE` | Lỗi | Request | File không đúng định dạng .xlsx. |
| `FILE_TOO_LARGE` | Lỗi | Request | File vượt quá dung lượng cho phép. |
| `WORKBOOK_CORRUPT` | Lỗi | Request | Không mở được file, file có thể bị lỗi. |
| `TEMPLATE_SHEET_MISSING` | Lỗi | Request | Không tìm thấy sheet MẪU trong file đích. |
| `NO_WEEK_SHEETS` | Lỗi | Request | File nguồn không có sheet tuần nào. |
| `JOB_NOT_FOUND` | Lỗi | Request | Phiên xử lý đã hết hạn, vui lòng upload lại. |
| `ANALYSIS_OUTDATED` | Lỗi | Request | Lựa chọn đã thay đổi, vui lòng phân tích lại. |
| `PROCESSING_TIMEOUT` | Lỗi | Request | Xử lý quá lâu, vui lòng thử lại với ít tuần hơn. |
| `TARGET_WEEK_SHEET_MISSING` | Chặn tuần | Tuần | Chưa có sheet TUẦN X — hãy copy sheet MẪU. |
| `TARGET_WEEK_HAS_DATA` | Chặn tuần | Tuần | Sheet TUẦN X đã có dữ liệu, bỏ qua. |
| `DUPLICATE_WEEK_SHEET` | Chặn tuần | Tuần | Có nhiều sheet cùng là TUẦN X. |
| `INVALID_SHEET_STRUCTURE` | Chặn tuần | Tuần | Sheet TUẦN X không đúng cấu trúc mẫu (ô …). |
| `INVALID_SOURCE_DATE` | Chặn tuần | Tuần | Không đọc được ngày tháng của TUẦN X trong file nguồn. |
| `SUBJECT_COUNT_MISMATCH` | Cảnh báo | Môn | Môn Toán: nguồn 5 tiết, đích 4 tiết — cần điền thủ công. |
| `AFFECTED_BY_DAY_OFF` | Cảnh báo | Môn | Môn Khoa học có tiết vào ngày nghỉ — cần điền thủ công. |
| `UNKNOWN_SUBJECT` | Cảnh báo | Môn | Môn "LS ĐL" chỉ có ở file nguồn. |
| `EMPTY_LESSON` | Cảnh báo | Tiết | Thứ Hai tiết 2 (Toán): tên bài trống. |
| `CONTENT_TOO_LONG` | Cảnh báo | Tiết | Nội dung dài, có thể bị khuất trong ô. |
| `SOURCE_WEEK_SHEET_MISSING` | Chặn tuần | Tuần | File nguồn không có sheet tuần n. |
| `INVALID_REQUEST` | Lỗi | Request | Chưa chọn tuần/môn nào. |
| `NOTHING_TO_GENERATE` | Lỗi | Request | Không có tuần/môn nào đủ điều kiện để điền. |
| `OUTPUT_VERIFY_FAILED` | Lỗi | Request | File kết quả không vượt qua bước tự kiểm tra (lỗi hệ thống, không trả file). |
| `VALIDATION_FAILED` | Lỗi | Request | Dữ liệu gửi lên không hợp lệ (chi tiết theo từng trường trong `details`). |
| `INVALID_CREDENTIALS` | Lỗi | Request | Email hoặc mật khẩu không đúng. |
| `UNAUTHENTICATED` | Lỗi (401) | Request | Vui lòng đăng nhập. |
| `TOO_MANY_ATTEMPTS` | Lỗi (429) | Request | Thử quá nhiều lần, vui lòng đợi một phút. |
| `CSRF_TOKEN_MISMATCH` | Lỗi (419) | Request | Phiên làm việc đã hết hạn, vui lòng tải lại trang. |
| `JOB_BUSY` | Lỗi (409) | Request | Phiên xử lý đang chạy, vui lòng đợi. |
| `RESULT_NOT_READY` | Lỗi (404) | Request | Chưa có file kết quả, vui lòng tạo file trước. |
| `PROCESSING_FAILED` | Lỗi (500) | Request | Có lỗi hệ thống khi xử lý file, vui lòng thử lại. |
| `NOT_FOUND` / `SERVER_ERROR` | Lỗi (404/500) | Request | Lỗi chung, không kèm chi tiết hệ thống. |

------------------------------------------------------------------------

# 10. Thiết kế frontend

## 10.1. Trang chính

Dashboard MVP đơn giản:

- Header: Teacher Workspace.
- Menu: Tổng quan, Lịch báo giảng.
- Thông tin tài khoản.
- Thẻ chức năng lịch báo giảng.
- Không hiển thị các module chưa triển khai như thể đã hoạt động.

## 10.2. Trang đồng bộ lịch báo giảng

Thiết kế dạng wizard 4 bước, có khung hướng dẫn chuẩn bị file đích ở đầu trang (mục 4.4), có thể thu gọn.

### Bước 1 — Upload file

Hai khu vực upload riêng: file nguồn, file đích.

Hiển thị:

- Tên file, dung lượng, trạng thái upload.
- Nút thay file.
- Thông báo chỉ hỗ trợ `.xlsx`.
- Nhắc: "File đích cần có sẵn các sheet tuần copy từ MẪU".

Không bắt buộc tên file phải chứa tên lớp.

### Bước 2 — Chọn tuần và môn

- Danh sách tuần tìm thấy trong file nguồn, kèm trạng thái sheet đích (Sẵn sàng / Chưa có sheet / Đã có dữ liệu).
- Chỉ cho chọn tuần có trạng thái Sẵn sàng; tuần khác hiển thị mờ kèm lý do.
- Chọn tất cả/bỏ chọn tất cả.
- Checklist môn cần đồng bộ, ví dụ ☑ Toán ☑ Tiếng Việt ☑ Khoa học ☐ Tiếng Anh…: tích môn nào thì đồng bộ môn đó. Lần đầu mặc định bỏ tích các môn bộ môn; HĐTV/HĐTT hiện thành một mục; nhớ lựa chọn trong `localStorage`.

### Bước 3 — Preview

Bảng theo tuần và môn:

| Tuần | Môn | Nguồn | Đích | Trạng thái |
|---|---|---:|---:|---|
| TUẦN 12 | Toán | 5 | 5 | Điền |
| TUẦN 12 | Tiếng Việt | 7 | 6 | Bỏ qua — lệch số tiết |
| TUẦN 12 | Khoa học | 2 | 2 | Bỏ qua — trùng ngày nghỉ |

- Mỗi tuần hiển thị ngày nghỉ phát hiện được; giáo viên có thể đánh dấu/bỏ đánh dấu, khi đó chạy lại analyze.
- Mở rộng từng môn để xem mapping (slot đích, tên bài, đồ dùng).
- Nút "Tạo file" enabled khi `can_generate = true`. Nếu có môn bị bỏ qua, nút ghi rõ "Tạo file (N môn cần điền thủ công)".

### Bước 4 — Kết quả

- Thành công/thất bại.
- Số sheet tuần đã điền.
- **Danh sách việc cần làm thủ công**: theo tuần → môn → lý do (có thể copy/in).
- Nút tải file Excel.
- Thông báo file tạm sẽ được xóa sau một thời gian.
- Nút tạo lượt xử lý mới.

## 10.3. Trạng thái UI

`idle` → `uploading` → `uploaded` → `analyzing` → `preview_ready` → `generating` → `completed`

Trạng thái lỗi: `upload_failed`, `analysis_failed`, `generate_failed`, `job_expired`.

Không cho gửi generate nhiều lần đồng thời cho cùng job.

## 10.4. Trải nghiệm lỗi

Thông báo lỗi cần hướng dẫn hành động tiếp theo, dùng thông báo trong danh mục mục 9.7. Không chỉ hiển thị "Có lỗi xảy ra".

Giao diện do chính Laravel phục vụ, nên khi Render đang ngủ thì lần tải trang đầu tiên sẽ chờ cold start; giao diện không thể hiện thông báo trong lúc này. Sau khi trang đã tải, nếu một request API chậm (ví dụ service vừa ngủ lại), hiển thị "Đang khởi động máy chủ, vui lòng chờ…" thay vì để giao diện treo.

------------------------------------------------------------------------

# 11. Quản lý file tạm

## 11.1. Cấu trúc thư mục

```text
storage/app/private/timetable-jobs/
└── {job_uuid}/
    ├── meta.json
    ├── source.xlsx
    ├── target.xlsx
    ├── request.json
    ├── weeks.json
    ├── analysis.json
    ├── generate.json
    └── result.xlsx
```

`meta.json`:

```json
{
  "job_id": "uuid",
  "owner": "user-id",
  "created_at": "2026-11-19T08:00:00+07:00",
  "expires_at": "2026-11-19T09:00:00+07:00",
  "status": "preview_ready",
  "source_file_name": "lich-bao-giang-5A.xlsx",
  "target_file_name": "lich-bao-giang-5B.xlsx",
  "source_sha256": "...",
  "target_sha256": "..."
}
```

Thư mục phải nằm ngoài public web root.

## 11.2. Vòng đời

- Upload tạo thư mục job và `meta.json`.
- Analyze ghi `request.json` và `analysis.json`.
- Generate tạo `result.xlsx`.
- Download trả `result.xlsx`.
- Cleanup xóa toàn bộ thư mục job.

## 11.3. Cleanup

Vì Render Free có thể ngủ/restart container, không dựa vào cron chạy đúng giờ.

- Cleanup job hết hạn mỗi khi tạo job mới (quét thư mục, đọc `expires_at`).
- Giới hạn số job đang tồn tại **\[ĐỀ XUẤT: tối đa 5\]**; vượt thì xóa job cũ nhất.
- Không lưu file lâu dài.
- **TTL \[ĐỀ XUẤT\]:** 60 phút. Lưu ý trên Render Free, job có thể mất sớm hơn khi service ngủ (khoảng 15 phút không có request).

## 11.4. Download và cleanup

Không xóa file trước khi response download hoàn tất. Giữ file đến hết TTL để giáo viên có thể tải lại, cleanup ở request sau.

------------------------------------------------------------------------

# 12. Bảo mật

## 12.1. Authentication \[ĐỀ XUẤT\]

MVP chỉ có một tài khoản không có nghĩa là bỏ authentication.

Phương án không cần database:

- Tài khoản cấu hình bằng environment: `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` (bcrypt/argon2 tạo sẵn bằng `php artisan tinker` hoặc lệnh riêng).
- Custom user provider đọc từ env thay cho Eloquent provider.
- `SESSION_DRIVER=cookie`: session mã hóa trong cookie bằng `APP_KEY` cố định, vẫn còn hiệu lực sau khi container restart.
- Giao diện và API cùng origin, nên dùng session guard chuẩn của Laravel (middleware `web`: session cookie + CSRF) cho các route `/api/v1/*` cần đăng nhập. Không cần Sanctum token, không cần bảng `personal_access_tokens`.
- CSRF bật đầy đủ: frontend lấy CSRF cookie trước khi login và gửi `X-XSRF-TOKEN`.

Yêu cầu chung:

- Không có đăng ký công khai.
- Mật khẩu chỉ lưu dạng hash.
- Rate limit login (ví dụ 5 lần/phút/IP).
- Cookie `Secure`, `HttpOnly`, `SameSite=Lax`.
- Có logout.
- Thời hạn session **\[ĐỀ XUẤT: 7 ngày\]** — cá nhân dùng, tránh phải đăng nhập lại liên tục.
- Mọi endpoint job yêu cầu auth và kiểm tra `owner` trong `meta.json`.
- Đổi `APP_KEY` sẽ làm mọi session hết hiệu lực — chấp nhận được.

## 12.2. Upload

- Chỉ nhận `.xlsx`.
- Kiểm tra nội dung file (ZIP hợp lệ, có cấu trúc OOXML).
- Giới hạn dung lượng và số file mỗi request.
- Lưu bằng tên cố định trong thư mục UUID.
- Không tin đường dẫn/tên file client.
- Không giải nén ZIP thủ công nếu không cần.
- Không chạy macro, không thực thi nội dung file.
- Có timeout và giới hạn tài nguyên cho Python.

## 12.3. Download

- Chỉ người dùng đã xác thực mới tải được.
- Không để output trong public storage.
- Không nhận arbitrary path.
- Không tạo URL công khai không hết hạn.

## 12.4. Secret

Secret chỉ nằm ở:

- Render Environment (hoặc file `.env` trên VPS, không commit).

Không commit: `.env`, `APP_KEY`, mật khẩu/hash mật khẩu, Gemini API key, token triển khai, thông tin tài khoản.

## 12.5. Dữ liệu học sinh

MVP xử lý lịch báo giảng, không cần gửi dữ liệu học sinh lên AI. Khi bổ sung AI:

- Ưu tiên ẩn danh hóa.
- Không gửi thông tin định danh học sinh nếu không cần.
- Cần chính sách lưu trữ/xóa dữ liệu.
- Cần thông báo rõ dữ liệu nào được gửi đến nhà cung cấp AI.

------------------------------------------------------------------------

# 13. Docker và triển khai Render

## 13.1. Mục tiêu Docker image

Một image chứa:

- Nginx.
- PHP-FPM và các PHP extension Laravel yêu cầu.
- Composer dependencies.
- Asset Vue đã build (`public/build`, từ stage Node của multi-stage build — mục 14).
- Python 3 và pip dependencies (`openpyxl` để đọc, `lxml` để ghi XML).
- LibreOffice headless **chỉ trong môi trường test/CI**, dùng cho test render; không đưa vào image production.
- Supervisor.
- Laravel application.

## 13.2. Runtime

Supervisor quản lý Nginx và PHP-FPM.

Nginx phải listen trên port do Render cung cấp qua `PORT`. Không hardcode port 80.

Không cần chạy Python daemon vì Laravel gọi script theo từng job.

## 13.3. Giới hạn upload và timeout — phải cấu hình đồng bộ

Giá trị mặc định của Nginx/PHP **nhỏ hơn** dung lượng upload cần thiết; không chỉnh thì upload sẽ lỗi.

| Lớp | Thiết lập | Giá trị đề xuất |
|---|---|---|
| Nginx | `client_max_body_size` | 12M (2 file × 5MB + dư) |
| PHP | `upload_max_filesize` | 6M |
| PHP | `post_max_size` | 12M |
| PHP | `memory_limit` | 256M |
| Nginx | `fastcgi_read_timeout` | 90s |
| PHP-FPM | `request_terminate_timeout` | 90s |
| Laravel | Symfony Process timeout | 60s |
| Laravel | `TIMETABLE_MAX_FILE_SIZE_MB` | 5 |

Thứ tự timeout: Process (60s) < PHP-FPM/Nginx (90s) < giới hạn request của Render, để lỗi được trả về có cấu trúc thay vì bị cắt kết nối.

**RAM:** openpyxl có thể dùng RAM gấp vài chục lần dung lượng file. Phải đo bộ nhớ với workbook thật ở Phase 2 để xác nhận giới hạn 5MB an toàn trong 512MB.

## 13.4. Entrypoint

Entrypoint có thể:

- Kiểm tra environment bắt buộc (`APP_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`).
- Tạo các thư mục runtime cần thiết.
- Set quyền thư mục storage/cache.
- Chạy `php artisan config:cache`, `route:cache`.
- Start Supervisor.

Không chạy migration vì MVP chưa dùng database.

Không chạy `php artisan key:generate` mỗi lần container start. `APP_KEY` phải là secret cố định.

## 13.5. Health check

Endpoint `/api/v1/health`:

- Trả trạng thái app.
- Không trả secret.
- Không phụ thuộc database.

## 13.6. Render environment

```dotenv
APP_ENV=production
APP_DEBUG=false
APP_KEY=base64:...
APP_URL=https://<render-service>.onrender.com
LOG_CHANNEL=stderr
LOG_LEVEL=info

ADMIN_EMAIL=...
ADMIN_PASSWORD_HASH=...

FILESYSTEM_DISK=local
SESSION_DRIVER=cookie
SESSION_LIFETIME=10080
SESSION_SECURE_COOKIE=true
CACHE_STORE=array
QUEUE_CONNECTION=sync

PYTHON_BINARY=/usr/bin/python3
TIMETABLE_TEMP_ROOT=/var/www/app/storage/app/private/timetable-jobs
TIMETABLE_MAX_FILE_SIZE_MB=5
TIMETABLE_JOB_TTL_MINUTES=60
TIMETABLE_MAX_JOBS=5
TIMETABLE_PROCESS_TIMEOUT=60
```

Các giá trị cụ thể phụ thuộc Dockerfile và Laravel version. Không copy nguyên `.env.example` lên Render mà không rà soát.

------------------------------------------------------------------------

# 14. Build giao diện trong Docker

Từ bản 1.5, giao diện Vue không deploy riêng lên Cloudflare Pages mà được build vào image Laravel.

- Dockerfile dùng **multi-stage**:
  - Stage `node`: `npm ci && npm run build` → tạo `public/build`.
  - Stage runtime: PHP-FPM + Nginx + Python, copy `public/build` từ stage `node`. Image runtime **không chứa Node**.
- Nginx phục vụ trực tiếp `public/build/*` (file tĩnh, cache dài vì tên file có hash); mọi request khác chuyển cho PHP-FPM.
- Không commit `public/build` và `public/hot`.
- Không đặt secret trong biến môi trường có tiền tố `VITE_`, vì chúng bị nhúng vào JavaScript gửi cho trình duyệt.

------------------------------------------------------------------------

# 15. Logging và quan sát hệ thống

Không cần hệ thống monitoring đắt tiền ở MVP, nhưng phải có log đủ để debug.

## 15.1. Log backend

Ghi:

- Job ID.
- Thời gian bắt đầu/kết thúc, tên bước.
- Thời gian Python chạy, bộ nhớ đỉnh nếu đo được.
- Kết quả thành công/thất bại, error code.
- Số tuần xử lý, số tiết được map, số môn bị bỏ qua.

Không log:

- Mật khẩu, `APP_KEY`, cookie/session.
- Toàn bộ nội dung giáo án nếu không cần.
- Dữ liệu nhạy cảm của học sinh.

## 15.2. Log Python

Python chỉ ghi log ra **stderr** dạng JSON line (stdout không dùng — mục 8.3). Laravel thu stderr và gắn job ID.

## 15.3. Job ID

Mỗi lượt xử lý có UUID riêng. Mọi log, lỗi và file tạm đều gắn với job ID.

------------------------------------------------------------------------

# 16. Kiểm thử

## 16.1. Unit test Python

- Normalize tên môn, tên sheet tuần (kể cả Unicode tổ hợp, số 0 ở đầu).
- Parse lesson record, target slot theo template profile.
- Group theo môn, giữ thứ tự.
- Count mismatch → môn bị bỏ qua, môn khác vẫn xử lý.
- Nhận diện ngày nghỉ; môn bị ảnh hưởng ở nguồn; môn bị ảnh hưởng chỉ ở đích (trường hợp số lượng khớp nhưng rơi vào ngày nghỉ).
- Ngày nghỉ chỉnh tay.
- Chỉ xử lý môn được chọn; mặc định bỏ chọn môn bộ môn.
- Nhóm HĐTV/HĐTT: đếm chung, ghép đúng thứ tự, ghi cột D theo nguồn (tuần chẵn `HĐTV` → `HĐTT`).
- Tiết trống/chữ "Nghỉ" (`HĐTN (SHDC)`, `TUẦN 3` HĐTV) → tiết nghỉ → môn bị bỏ qua, có cảnh báo `EMPTY_LESSON`.
- Ngày nghỉ dạng vùng gộp `E23:F28` để trống (`TUẦN 7`) → buổi nghỉ cả ngày; môn có slot đích hôm đó bị bỏ qua.
- File nguồn có vùng gộp thêm ở cột E:F không bị coi là sai cấu trúc.
- Ghép tên bài và đồ dùng.
- Nguồn trống → đích trống (ghi đè nội dung mặc định).
- Xử lý môn đặc biệt.
- Xử lý ngày tháng và tiêu đề tuần.
- Phân loại trạng thái sheet tuần: `ready`, `has_data`, `missing`, `invalid_structure`, `duplicate`.

## 16.2. Integration test Excel

Dùng bản sao workbook thực tế đã ẩn dữ liệu nhạy cảm.

1. Nguồn/đích có số tiết khớp toàn bộ.
2. Một môn nguồn nhiều tiết hơn đích → chỉ môn đó bị bỏ qua.
3. Một môn đích nhiều slot hơn nguồn → chỉ môn đó bị bỏ qua.
4. Tuần có ngày nghỉ lễ.
5. Thiếu sheet tuần trong file đích.
6. Sheet tuần đích đã có dữ liệu.
7. Hai sheet cùng số tuần.
8. Sheet tuần đích sai cấu trúc.
9. Thiếu sheet `MẪU`.
10. Tên môn có khoảng trắng thừa, alias, chỉ có ở một phía.
11. Tên bài dài.
12. Đồ dùng trống trong khi `MẪU` có nội dung mặc định.
13. Tuần có merged cells.
14. Sheet tuần có TKB khác `MẪU` (giáo viên đã sửa).
15. Upload file kết quả lần trước làm file đích (làm việc tăng dần).
16. Workbook lỗi/corrupt; file không phải `.xlsx`.

## 16.3. Test bảo toàn định dạng

Theo ba mức ở mục 5.4:

- Part ngoài các sheet được ghi: giống nguyên byte.
- Sheet được ghi: diff XML chỉ nằm ở nội dung các ô trong whitelist; thuộc tính `s` không đổi.
- Render LibreOffice → PDF: trang của sheet không ghi giống từng pixel.
- Sheet `MẪU` không đổi; không sheet nào bị thêm/bớt/đổi tên.
- Workbook mở lại được bằng openpyxl và giá trị đọc lại đúng mapping.
- **Thủ công trước khi nghiệm thu:** mở file kết quả bằng Microsoft Excel (và WPS nếu giáo viên dùng), xem bản in thử.

## 16.4. Test Laravel

- Upload hợp lệ, thiếu file, sai định dạng, vượt dung lượng.
- API không có auth → 401.
- Generate khi `can_generate = false`.
- Generate với request khác analyze → `ANALYSIS_OUTDATED`.
- Download job không thuộc user; job hết hạn; job không tồn tại.
- Python timeout, Python exit code 1 và 2.
- Cleanup job hết hạn; giới hạn số job.

## 16.5. Test end-to-end

Trên browser (máy tính và điện thoại):

1. Đăng nhập.
2. Upload nguồn và đích.
3. Chọn tuần và môn.
4. Analyze, xem preview, chỉnh ngày nghỉ.
5. Generate.
6. Download.
7. Mở file bằng Excel/LibreOffice, đối chiếu format và nội dung.
8. Kiểm tra trường hợp backend đang ngủ (cold start).

------------------------------------------------------------------------

# 17. Tiêu chí nghiệm thu MVP

## Hạ tầng

- [ ] Frontend truy cập được qua HTTPS.
- [ ] Backend Render hoạt động.
- [ ] Giao diện và API chạy cùng domain trên Render (kể cả upload và download file).
- [ ] Laravel gọi được Python.
- [ ] Không có secret trong repository/frontend.
- [ ] Có health endpoint.

## Xác thực

- [ ] Người chưa đăng nhập không dùng được API nghiệp vụ.
- [ ] Đăng nhập sai bị giới hạn.
- [ ] Đăng xuất hoạt động.
- [ ] Phiên đăng nhập vẫn còn sau khi backend restart.
- [ ] Job không thể bị người khác tải nếu không có quyền.

## Excel

- [ ] Upload được hai file `.xlsx`.
- [ ] Đọc được danh sách tuần nguồn kèm trạng thái sheet đích.
- [ ] Chỉ xử lý sheet tuần `ready`; bỏ qua sheet chưa có hoặc đã có dữ liệu, có thông báo.
- [ ] Chọn nhiều tuần; mỗi tuần xử lý độc lập.
- [ ] Tích chọn được môn cần đồng bộ; chỉ môn được chọn bị ghi; môn bộ môn mặc định bỏ tích.
- [ ] HĐTV/HĐTT ghép đúng ở cả tuần chẵn và tuần lẻ.
- [ ] Tiết trống/nghỉ: môn đó không bị ghi, có cảnh báo rõ tiết nào trống.
- [ ] Phân phối theo môn, không theo vị trí dòng nguồn.
- [ ] Giữ đúng thứ tự tiết trong từng môn.
- [ ] Tên bài và đồ dùng đi cùng nhau.
- [ ] Môn lệch số tiết bị bỏ qua, các môn khác vẫn được điền.
- [ ] Tuần có ngày nghỉ: môn bị ảnh hưởng (ở nguồn hoặc đích) bị bỏ qua, có thông báo.
- [ ] Nguồn trống → đích trống.
- [ ] Ngày tháng và tiêu đề tuần lấy từ nguồn.
- [ ] Sheet `MẪU` không bị sửa; không sheet nào bị thêm/xóa/đổi tên.
- [ ] Định dạng mọi sheet giữ nguyên.
- [ ] Không tự bù tuần khác.
- [ ] Không ghi đè file nguồn/đích.
- [ ] Output mở được bằng Excel/LibreOffice.

## Trải nghiệm

- [ ] Có hướng dẫn chuẩn bị file đích.
- [ ] Có preview.
- [ ] Có thông báo lỗi rõ, theo danh mục mã lỗi.
- [ ] Có danh sách việc cần điền thủ công sau khi tạo file.
- [ ] Có nút tải file.
- [ ] Có trạng thái xử lý, kể cả khi backend đang khởi động.
- [ ] Có cleanup file tạm.

------------------------------------------------------------------------

# 18. Rủi ro và phương án giảm thiểu

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Render cold start | Request đầu chậm (~1 phút) | Gọi health sớm, hiển thị trạng thái; nâng gói/VPS khi cần |
| Service ngủ/restart | Mất file tạm giữa chừng | Không lưu lâu dài; báo `JOB_NOT_FOUND`, upload lại |
| RAM thấp | Excel lớn có thể lỗi | Giới hạn 5MB; đo RAM với workbook thật |
| openpyxl save làm đổi style ô gộp và chiều cao dòng (đã xác nhận ở Phase 0) | Sai định dạng file đích | Ghi bằng sửa trực tiếp XML; test byte/XML/pixel |
| Sửa XML sai làm file không mở được | Hỏng file kết quả | Chỉ sửa phần tử `<c>` có sẵn; test mở lại bằng openpyxl và LibreOffice; nghiệm thu bằng Excel |
| HĐTV/HĐTT thay phiên theo tuần | Bỏ qua môn mỗi tuần chẵn | Nhóm hoán đổi, ghi cột D theo nguồn (mục 4.10) |
| Giáo viên copy sai sheet hoặc sửa cấu trúc | Ghi sai ô | Kiểm tra `structure_anchors`, trạng thái `invalid_structure` |
| Môn có alias | Match sai | Alias config rõ ràng; ghép tay trong preview |
| Số tiết không khớp | Thiếu nội dung | Bỏ qua môn, báo rõ để điền thủ công |
| Ngày nghỉ, số lượng vẫn khớp | Điền bài vào ngày nghỉ | Xét ngày nghỉ ở cả nguồn và đích |
| Nhận diện ngày nghỉ sai | Bỏ sót hoặc bỏ thừa môn | Cho giáo viên chỉnh ngày nghỉ trong preview |
| Ô ngày là công thức | Hiển thị trống trên một số trình xem | Xác nhận ở Phase 0, quyết định ghi giá trị hay giữ công thức |
| Nội dung dài | Khó đọc trong ô | Cảnh báo, không tự đổi format |
| Cấu hình upload/timeout sai | Upload lỗi, timeout không rõ | Bảng cấu hình mục 13.3, test E2E |
| Giới hạn upload Nginx/PHP chưa chỉnh | Upload lỗi | Bảng cấu hình mục 13.3; E2E test multipart và binary |
| Người khác truy cập URL | Lộ file | Authentication, kiểm tra owner, private storage |

------------------------------------------------------------------------

# 19. Kế hoạch triển khai từng bước

## Phase 0 — Xác nhận đầu vào

1. ✅ Có file mẫu `LBG_mau.xlsx` (`MẪU` + 9 tuần); file nguồn và đích cùng bố cục.
2. ✅ Kiểm tra cấu trúc sheet; xác định sheet `MẪU`.
3. ✅ Xác định ô ngày tháng, ô tiêu đề tuần, ô ngày ký: đều là chuỗi, không có công thức (mục 4.11).
4. ✅ Xác định dòng của từng ngày/buổi, cột môn, tên bài, đồ dùng (mục 8.2).
5. ✅ Quy tắc nghỉ: không có nội dung hoặc có chữ "Nghỉ" (mục 4.8).
6. ✅ Lấy danh sách tên môn thực tế (mục 4.10); chốt môn bộ môn mặc định, nhóm HĐTV/HĐTT, xử lý tiết trống.
7. ✅ Bản đầu `template_profile.json`, `subject_config.json` (mục 8.2, 8.8).
8. ✅ Test round-trip: openpyxl làm đổi định dạng → chọn writer sửa XML trực tiếp; prototype đạt giống từng pixel (mục 5.3).
9. ✅ Bộ file test: `TUẦN 8.xlsx` (lớp đích, TKB khác, ô môn `HĐTV/HĐTT`); `LBG_mau.xlsx`/`TUẦN 7` có ngày nghỉ thứ Năm. ⏳ Còn thiếu: một tuần có môn lệch số tiết (có thể tự tạo từ file mẫu).
10. ✅ Prototype đầy đủ (analyze + ghép + ghi XML) chạy trên dữ liệu thật; kết quả ở thư mục `docs/phase0/`. Sheet `MẪU` của file kết quả render giống từng pixel; chỉ part XML của sheet `TUẦN 8` thay đổi. ⏳ Giáo viên mở bằng Excel/WPS để xác nhận cuối.

Ghi chú: `TUẦN 8.xlsx` và bản `LBG_mau.xlsx` mới được lưu lại bằng công cụ khác (vùng dữ liệu `A1:F1000`, kiểu file xuất từ Google Sheets). Reader dùng tọa độ cố định nên không bị ảnh hưởng; writer sửa XML vẫn hoạt động.

## Phase 1 — Khởi tạo repository ✅

1. ✅ GitHub repository `teacher-workspace` (đã có remote).
2. ✅ Vue 3 + Vite 6 trong `frontend` (vue-router, pinia, axios). Vite 6 vì máy dev dùng Node 20.11; Vite 7 cần Node 20.19+.
3. ✅ Laravel 13 API trong `backend`, prefix `/api/v1`, endpoint `/api/v1/health`. Đã bỏ phần giao diện web mặc định; tắt `serve` của disk `local` để không lộ file private qua URL.
4. ✅ Thư mục Python: CLI `process_timetable.py` (lệnh `check`; các lệnh job trả `NOT_IMPLEMENTED` theo đúng hợp đồng mục 8.3), `config/*.json`, fixtures là 2 file Excel thật.
5. ✅ `.gitignore`, README, `CLAUDE.md`.
6. ✅ Chạy local: Laravel `:8000`, Vite `:5173`, `/api/v1/health` qua proxy Vite trả `ok`.
7. ✅ (v1.5) Gộp giao diện vào Laravel: Laravel ở thư mục gốc, Vue trong `resources/js`, Python trong `python/`. `php artisan serve` phục vụ cả SPA (bản build hoặc Vite dev) và API; test Laravel 7/7, Python 8/8.

Test: Laravel 4/4, Python 8/8 (gồm test đối chiếu `template_profile.json` với 2 file Excel thật), `npm run build` thành công.

## Phase 2 — Python Excel engine local

1. ✅ Reader (kiểm tra gói zip chống zip bomb; openpyxl + `defusedxml`) và parser theo template profile.
2. ✅ Normalization (NFC, khoảng trắng, alias, nhóm hoán đổi, số tuần).
3. ✅ Day-off detector (tiết nghỉ, buổi nghỉ, chỉnh tay theo buổi/ngày).
4. ✅ Matcher theo môn (mục 4.6–4.10).
5. ✅ Validator: cấu trúc sheet (nguồn cho phép vùng gộp E:F đánh dấu nghỉ, đích phải đúng mẫu), trạng thái sheet đích, ngày tháng nguồn.
6. ✅ Writer sửa XML: whitelist ô, parser lxml an toàn, từ chối ô thiếu/ô có công thức, tự kiểm tra sau khi ghi (byte, style, đọc lại giá trị).
7. ✅ CLI `list-weeks` / `analyze` / `generate` theo hợp đồng mục 8.3; file kết quả ghi atomic.
8. ✅ 74 test (unit + chạy CLI end-to-end trên 2 file thật + render LibreOffice so pixel).
9. ✅ Đo với file thật (9 tuần): mỗi lệnh < 0,4 giây, RAM tối đa ~35MB.
10. ✅ Đối chiếu định dạng: chỉ part XML của sheet được ghi thay đổi; sheet không ghi render giống từng pixel.

Ghi chú triển khai:
- Tên bài/đồ dùng được copy **nguyên văn** (giữ dấu cách đầu/cuối, xuống dòng) nhưng chuẩn hóa Unicode về NFC. File nguồn mẫu có chữ ở dạng tổ hợp (NFD); hiển thị không đổi.
- Lệnh `generate` dùng lại `writes` trong `analysis.json` và chỉ chạy khi request và hash hai file trùng với lúc phân tích.

Chỉ chuyển sang deploy khi xử lý Excel local đúng.

## Phase 3 — Laravel orchestration

1. ✅ Auth: `App\Auth\EnvUserProvider` (driver `env`, đọc `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`), session cookie, CSRF. Nhóm middleware `api` được thêm cookie + session + CSRF (`bootstrap/app.php`) vì giao diện và API cùng origin. Lệnh `php artisan admin:password` tạo mã băm mật khẩu.
2. ✅ Upload: kiểm tra đuôi `.xlsx`, dung lượng, chữ ký zip `PK`; job UUID, thư mục quyền 0700, `meta.json` (owner, hạn, hash, tên file đã làm sạch).
3. ✅ Sau upload chạy `list-weeks`, trả tuần + môn + môn tích sẵn. Engine báo lỗi nghiệp vụ → xóa job ngay.
4. ✅ Analyze/generate qua `Process` (Symfony Process), timeout cấu hình; khóa job bằng `flock` (`JOB_BUSY`); analyze lại thì xóa `result.xlsx` cũ.
5. ✅ Đổi mã thoát Python → lỗi API: 1 → mã lỗi của engine (422, riêng `ANALYSIS_OUTDATED` 409); khác/timeout → `PROCESSING_FAILED` 500 / `PROCESSING_TIMEOUT` 504. Log stderr Python kèm job ID.
6. ✅ Download: tên file `<tên file đích>_dongbo_<yyyymmdd-hhmm>.xlsx` (giờ Việt Nam), `no-store`, `nosniff`; tải lại được tới khi job hết hạn.
7. ✅ Cleanup: xóa job hết hạn mỗi lần tạo job mới hoặc khi truy cập; giới hạn số job (xóa job cũ nhất); job của người khác/không tồn tại/hết hạn đều trả `JOB_NOT_FOUND`.
8. ✅ Test: 33 test Laravel (auth, rate limit, định dạng lỗi, upload, toàn bộ luồng với engine Python thật, quyền sở hữu, hết hạn, giới hạn job, lỗi engine). Kiểm tra thủ công qua HTTP thật: thiếu CSRF token → 419; đủ luồng login → upload → analyze → generate → download → logout.

## Phase 4 — Frontend

1. ✅ Layout (menu, email, đăng xuất), trang đăng nhập thật, dashboard. Router chặn trang khi chưa đăng nhập, sau đăng nhập quay lại trang định vào; hết phiên (401) → về trang đăng nhập.
2. ✅ Khung hướng dẫn copy sheet MẪU (thu gọn được).
3. ✅ Wizard 4 bước (`resources/js/components/sync/`, store `stores/sync.js` theo trạng thái mục 10.3):
   - Bước 1: hai ô chọn file (kéo thả được), kiểm tra `.xlsx`/5MB phía trình duyệt, thanh tiến trình upload.
   - Bước 2: tuần kèm trạng thái và lý do, chỉ chọn được tuần Sẵn sàng; checklist môn, nhớ lựa chọn trong `localStorage`.
   - Bước 3: bảng môn theo tuần, mở xem từng tiết sẽ điền (kèm đổi tên HĐTV/HĐTT), nút bật/tắt nghỉ theo ngày (chạy lại analyze), nút “Tạo file (N môn cần điền thủ công)”.
   - Bước 4: tải file, danh sách việc thủ công theo tuần (sao chép/in), làm lượt mới (xóa job trên máy chủ).
4. ✅ Tích hợp API: axios gửi `X-XSRF-TOKEN`; lỗi hiển thị bằng thông báo tiếng Việt của API.
5. ✅ Loading/lỗi/cold start: thông báo “Đang khởi động máy chủ…” khi request > 6 giây; `JOB_NOT_FOUND` → về bước 1 kèm hướng dẫn upload lại. Tải lại trang giữ job (mã job lưu trong `sessionStorage`, lấy lại qua `GET /jobs/{id}`, quay về bước 2). Đăng xuất xóa job đang dở.
6. ✅ Kiểm tra trên Chrome headless (puppeteer, ngoài repo): toàn bộ luồng với 2 file thật, sai mật khẩu, bật nghỉ thứ Hai → Toán bị bỏ qua, tải file 255KB đúng định dạng, tải lại trang, job hết hạn, màn hình 390px không tràn ngang. Test đơn vị JS bằng Vitest (`npm test`).

Ghi chú: `list-weeks`/upload trả thêm `days` (nhãn ngày và buổi từ `template_profile.json`) để giao diện vẽ nút ngày nghỉ, không viết cứng bố cục trong frontend.

## Phase 5 — Deploy

1. ✅ `Dockerfile` multi-stage: `node:20` build asset → `composer:2` (không dev) → runtime `php:8.3-fpm-bookworm` + Nginx + Supervisor + Python 3.11 (venv `/opt/venv`). Cấu hình trong `docker/`: `nginx.conf.template` (cổng `${PORT}`, upload 12MB, timeout 90s, cache `/build/` 1 năm, chặn dotfile và file `.php` khác, header bảo mật), `php.ini`, `php-fpm.conf` (4 worker, timeout 90s, `clear_env = no`), `supervisord.conf`, `entrypoint.sh` (bắt buộc `APP_KEY`/`ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH`, `APP_URL` mặc định từ `RENDER_EXTERNAL_URL`, cache config/route/view, không migrate, không `key:generate`). `.dockerignore` loại `.env`, `vendor`, `node_modules`, test, docs.
2. ✅ Build/test Docker local: thiếu secret → container dừng kèm thông báo; 73 test Python chạy trong image (1 test render LibreOffice bỏ qua vì image không có LibreOffice); toàn bộ kịch bản trình duyệt chạy với container giới hạn 512MB — RAM đỉnh **86MB**; `/.env` → 403. Sửa 2 lỗi phát hiện khi chạy container: (a) `fastcgi_params` của Debian bỏ số cổng khỏi `HTTP_HOST` làm sai URL asset khi chạy local → gửi `$http_host`; (b) lỗi nghiệp vụ (`ApiException`) bị ghi log ERROR → `dontReport`.
3. ⏳ Tạo Render Web Service từ `render.yaml` (Blueprint, gói Free, Singapore, `autoDeploy`), nhập 3 biến bí mật — **người dùng thực hiện**, hướng dẫn trong `docs/deployment.md`.
4. ⏳ Deploy, kiểm tra `/api/v1/health` và trang giao diện.
5. ⏳ Kiểm tra upload/download trên domain Render.
6. ⏳ Kiểm tra cold start.

Thay đổi ứng dụng kèm theo: `trustProxies(at: '*')` (IP thật cho giới hạn đăng nhập, URL `https`, cookie `Secure` sau proxy Render); đổi middleware CSRF sang `PreventRequestForgery` (tên mới của `ValidateCsrfToken` trong Laravel 13).

## Phase 6 — Bảo mật và nghiệm thu

1. Kiểm tra session/cookie/CSRF.
2. Rate limit.
3. Upload validation.
4. Private download.
5. Cleanup.
6. Kiểm thử workbook thật.
7. Kiểm thử trên máy tính và điện thoại.
8. Kiểm tra backup source code và cấu hình.
9. Viết `docs/user-guide.md` cho giáo viên.

------------------------------------------------------------------------

# 20. Các quyết định

## 20.1. Đã chốt

| Hạng mục | Quyết định |
|---|---|
| Định dạng file | Chỉ `.xlsx` |
| Tạo sheet tuần | Giáo viên tự copy `MẪU` trong Excel; hệ thống chỉ ghi giá trị |
| Sheet tuần đã có dữ liệu | Không xử lý, thông báo |
| Sheet tuần chưa có | Không xử lý, hướng dẫn copy `MẪU` |
| Số tiết không khớp | Bỏ qua môn đó, các môn khác vẫn xử lý, thông báo để điền thủ công |
| Tuần có ngày nghỉ | Thông báo; chỉ xử lý các môn không bị ảnh hưởng |
| Môn GV bộ môn | Mặc định không đồng bộ; giáo viên bật/tắt khi chọn môn |
| Ô nguồn trống | Ô đích để trống (kể cả khi `MẪU` có nội dung mặc định) |
| Bố cục file | Nguồn và đích cùng bố cục, tọa độ ô cố định (mục 8.2) |
| Nhận diện nghỉ | Tiết không có tên bài hoặc có chữ "Nghỉ" là tiết nghỉ; cả buổi nghỉ là buổi nghỉ (mục 4.8) |
| Tiết trống / tiết nghỉ | Không xử lý môn đó trong tuần; cảnh báo `EMPTY_LESSON` |
| Chọn môn đồng bộ | Giáo viên tích chọn môn nào thì đồng bộ môn đó; mặc định bỏ tích các môn bộ môn (chữ đỏ) |
| HĐTV / HĐTT | Nhóm hoán đổi; ghi cả ô môn (cột D) theo nguồn |
| Ô ngày tháng | Copy nguyên văn `A1`, `A3…A29`, `E35` từ nguồn sau khi kiểm tra |

## 20.2. Đề xuất, chờ xác nhận

| Hạng mục | Đề xuất mặc định | Trạng thái |
|---|---|---|
| Repository | Repo `teacher-workspace` trên GitHub | \[ĐÃ CHỐT\] |
| Hosting | Một Docker image trên Render Free, phục vụ cả giao diện và API (thay thế: VPS nhỏ) | \[ĐỀ XUẤT\] |
| Database MVP | Chưa dùng | \[ĐỀ XUẤT\] |
| Authentication | Một tài khoản trong env, session cookie | \[ĐỀ XUẤT\] |
| Thời hạn session | 7 ngày | \[ĐỀ XUẤT\] |
| AI | Để giai đoạn sau | \[ĐỀ XUẤT\] |
| File upload limit | 5MB/file | \[ĐỀ XUẤT\] |
| Job TTL | 60 phút | \[ĐỀ XUẤT\] |
| Ghép tay tên môn trong preview | Có, chỉ áp dụng cho lượt xử lý hiện tại | \[ĐỀ XUẤT\] |

## 20.3. Kết quả Phase 0 và câu hỏi còn mở

Đã xác định từ `LBG_mau.xlsx`:

| Hạng mục | Kết quả |
|---|---|
| Template profile | Tọa độ cố định (mục 8.2) \[ĐÃ CHỐT\] |
| Ô ngày tháng | Chuỗi văn bản, không công thức; copy nguyên văn từ nguồn (mục 4.11) |
| Nghỉ | Không có nội dung hoặc có chữ "Nghỉ" \[ĐÃ CHỐT\] (mục 4.8) |
| Tên môn | 17 tên thực tế (mục 4.10) |
| Round-trip | openpyxl làm đổi định dạng → ghi bằng sửa XML (mục 5.3) |

Các câu hỏi về môn bộ môn, HĐTV/HĐTT, `HĐTN (SHDC)`, tiết trống đã được chốt (mục 20.1).

Còn mở:

| # | Việc | Ghi chú |
|---|---|---|
| 1 | ~~Gửi file lớp khác và tuần nghỉ lễ~~ | ✅ Đã có `TUẦN 8.xlsx`, `TUẦN 7` |
| 2 | Mở `docs/phase0/TUAN8_ket-qua_*.xlsx` bằng Microsoft Excel/WPS để xác nhận định dạng | Nghiệm thu cách ghi XML |

------------------------------------------------------------------------

# 21. Hướng mở rộng sau MVP

## Giai đoạn 1.5 — Tiện ích lịch báo giảng

- Tùy chọn tự động copy sheet `MẪU` để tạo sheet tuần còn thiếu. Không dùng openpyxl (Phase 0 đã chứng minh làm đổi định dạng); nếu làm thì nhân bản part XML của `MẪU` và cập nhật `workbook.xml`, rels, `[Content_Types].xml`, `docProps/app.xml`.
- Tùy chọn **dồn bài sang tuần sau**: coi bài của mỗi môn là hàng đợi liên tục qua nhiều tuần, giải quyết lệch số tiết và nghỉ lễ mà không phải điền tay.
- Nhiều sheet mẫu (`MẪU HK1`, `MẪU HK2`).
- Lưu cấu hình môn phía server khi đã có database.

## Giai đoạn 2 — Database và thư viện tài liệu

- Thêm PostgreSQL.
- Thêm object storage.
- Tạo document metadata.
- Phân loại theo năm học, khối, môn, bài, loại tài liệu.
- Tìm kiếm keyword.
- Lưu version tài liệu.
- **Định hướng:** lưu phân phối chương trình (PPCT) và thời khóa biểu trong database để tự sinh lịch báo giảng, không còn phụ thuộc file của lớp khác. Mô hình lesson record/target slot của MVP nên đặt tên và cấu trúc sẵn cho hướng này.

## Giai đoạn 3 — AI trợ lý giáo viên

- Tích hợp Gemini API ở backend.
- API key chỉ nằm server-side.
- AI có thể tham khảo tài liệu đã lưu, trả lời kèm nguồn tài liệu nội bộ.
- Lưu lịch sử hội thoại khi đã có database.
- Có cơ chế kiểm tra nội dung và chỉnh sửa nhiều vòng.
- Không để AI tự sửa workbook nghiệp vụ nếu không có validation.

## Giai đoạn 4 — Nhiều giáo viên/trường

- User management, school/organization, class/academic year.
- Role/permission, data isolation theo user/trường.
- Template profile riêng theo trường.
- Audit log, storage quota, backup/restore.

## Giai đoạn 5 — Tách worker nếu tải tăng

- Thêm queue và worker service.
- Có thể tách Python thành service riêng.
- Dùng object storage để chia sẻ file giữa web và worker.
- Thêm trạng thái job và retry có kiểm soát.

Không cần làm trước khi có nhu cầu.

------------------------------------------------------------------------

# 22. Checklist dành cho Claude Code

Nội dung này sẽ được đưa vào `CLAUDE.md` của repository.

1. Đọc toàn bộ tài liệu trước khi code.
2. Không tự ý mở rộng scope.
3. Không tự thêm database, queue, Redis hoặc microservice vào MVP nếu chưa có yêu cầu.
4. Không hardcode tọa độ ô Excel trong code; dùng `template_profile.json`.
5. Không dùng AI để phân phối tiết học.
6. Không copy dữ liệu theo vị trí dòng nguồn.
7. Không tạo, xóa, đổi tên sheet; không copy sheet `MẪU` bằng code trong MVP.
8. Không thay đổi sheet `MẪU`.
9. Đọc bằng openpyxl, **ghi bằng sửa trực tiếp XML** (mục 5.3); không dùng `openpyxl.save()` cho file kết quả; không đổi style; không copy style từ file nguồn.
10. Không ghi đè file nguồn hoặc file đích.
11. Khi không chắc chắn (lệch số tiết, ngày nghỉ, tên môn lạ): bỏ qua và báo, không đoán.
12. Mọi môn/tuần bị bỏ qua phải có mã lỗi và thông tin cụ thể.
13. Có unit test và integration test.
14. Không commit secret.
15. Không đưa file upload vào public directory.
16. Triển khai từng phase, sau mỗi phase chạy test và báo kết quả.
17. Nếu yêu cầu chưa rõ, hỏi lại thay vì tự suy diễn.
18. Ưu tiên code dễ đọc, có type/validation, tách service rõ ràng.
19. Không tạo abstraction quá mức cho một chức năng duy nhất.
20. Không đánh dấu hoàn thành nếu chưa chạy test hoặc chưa xác nhận kết quả.
21. Khi hoàn thành mỗi phase, cập nhật README và tài liệu triển khai.

------------------------------------------------------------------------

# 23. Tài liệu tham khảo chính thức

Các giới hạn và giao diện nhà cung cấp có thể thay đổi. Kiểm tra lại trước khi deploy:

- Laravel Vite: https://laravel.com/docs/vite
- Render: https://render.com/docs
- Render pricing: https://render.com/pricing
- Render Docker: https://render.com/docs/docker
- Laravel deployment: https://laravel.com/docs/deployment
- Laravel Process: https://laravel.com/docs/processes
- Laravel CSRF protection: https://laravel.com/docs/csrf
- Laravel authentication (custom user provider): https://laravel.com/docs/authentication
- Laravel filesystem: https://laravel.com/docs/filesystem
- openpyxl: https://openpyxl.readthedocs.io/

------------------------------------------------------------------------

# 24. Kết luận

Kiến trúc MVP:

- **Frontend:** Vue 3 SPA trong `resources/js`, build bằng Vite, phục vụ bởi Laravel.
- **API:** Laravel trên Render Docker Web Service.
- **Excel engine:** Python, Laravel gọi bằng Symfony Process; đọc bằng openpyxl, ghi giá trị vào sheet tuần giáo viên đã chuẩn bị bằng cách sửa trực tiếp XML.
- **Database:** chưa cần cho luồng xử lý file ban đầu.
- **Storage:** file tạm trong vòng đời job, không lưu lâu dài.
- **Authentication:** cần có ngay, dù chỉ một người dùng; tài khoản trong env, session cookie.
- **AI:** để giai đoạn sau.

Mục tiêu là đưa được chức năng lịch báo giảng lên online với chi phí thấp nhất, đồng thời giữ kiến trúc đủ sạch để phát triển thành Teacher Workspace đầy đủ trong tương lai.

**Thứ tự ưu tiên:** xác nhận workbook thực tế và test round-trip → làm Excel engine chạy đúng local → tích hợp Laravel → hoàn thiện UI → deploy → bảo mật và nghiệm thu.

Không nên bắt đầu bằng việc deploy hạ tầng trước khi chứng minh được thuật toán Excel chạy đúng với hai file thật.
