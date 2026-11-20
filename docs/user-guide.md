# Hướng dẫn sử dụng — Đồng bộ lịch báo giảng

Địa chỉ: **https://teacher-workspace-lr8u.onrender.com**

Chức năng này lấy **tên bài** và **đồ dùng dạy học** từ lịch báo giảng của một lớp khác (file nguồn) rồi điền vào lịch
báo giảng của lớp bạn (file đích), **theo đúng thời khóa biểu của lớp bạn**. Định dạng file của bạn được giữ nguyên.

---

## 1. Chuẩn bị file (trên máy tính, bằng Excel)

**File nguồn:** lịch báo giảng của lớp khác, đã có tên bài các tuần cần lấy. Không cần sửa gì.

**File đích:** lịch báo giảng của lớp bạn. Với mỗi tuần muốn điền:

1. Chuột phải vào sheet **MẪU** → **Move or Copy** (Di chuyển hoặc Sao chép).
2. Tích **Create a copy** (Tạo bản sao) → **OK**.
3. Đổi tên sheet vừa tạo thành tên tuần, ví dụ **TUẦN 12** (số tuần giống file nguồn).
4. Nếu tuần đó thời khóa biểu khác bình thường, sửa luôn cột **Môn** trên sheet tuần đó.
5. Lưu file dạng **.xlsx**.

> Nếu file của bạn là `.xls`, mở bằng Excel → **File → Save As** → chọn **Excel Workbook (.xlsx)**.

## 2. Đăng nhập

Mở địa chỉ trên bằng trình duyệt máy tính (Chrome hoặc Edge), nhập email và mật khẩu.

> Nếu trang trắng hoặc quay lâu khi vừa mở: hệ thống đang "thức dậy" sau thời gian không dùng — đợi khoảng 1 phút.

## 3. Đồng bộ — 4 bước

Vào menu **Lịch báo giảng**.

**Bước 1 — Tải file:** chọn (hoặc kéo thả) **File nguồn** và **File đích**, bấm **Tải lên và đọc file**.

**Bước 2 — Chọn tuần và môn:**

- Các ô **Tuần**: ô trắng là tuần chọn được, ô xanh là tuần đang chọn. Ô viền nét đứt là tuần chưa dùng được (chấm cam:
  file đích chưa có sheet tuần đó; chấm xám: sheet đã có dữ liệu). Dòng nhắc bên dưới nói rõ cần làm gì.
- Các ô **Môn**: tích môn nào thì điền môn đó. Nút **Mặc định** bỏ các môn giáo viên bộ môn dạy. Lựa chọn được nhớ cho lần sau.
- Bấm **Phân tích và xem trước**.

**Bước 3 — Xem trước:**

- Mỗi môn hiện **Điền** (xanh) hoặc **Bỏ qua** (cam) kèm lý do. Bấm vào một môn để xem từng tiết sẽ điền.
- Hàng **Ngày nghỉ**: nếu tuần có ngày nghỉ mà hệ thống chưa nhận ra (hoặc nhận nhầm), bấm vào ngày đó để đổi
  *Đi học ↔ Nghỉ*. Hệ thống tự phân tích lại.
- Bấm **Tạo file**.

**Bước 4 — Kết quả:**

- Bấm **Tải file Excel** để tải file kết quả về máy. File gốc của bạn không bị thay đổi.
- Mục **Việc cần làm thủ công** liệt kê các môn chưa được điền — mở file kết quả và điền tay (có nút **Sao chép**, **In**).
- **Làm lượt mới** để xử lý file khác.

## 4. Vì sao một môn bị "Bỏ qua"?

Hệ thống chỉ điền khi chắc chắn đúng. Khi không chắc, nó bỏ qua môn đó trong tuần đó để bạn tự điền:

| Lý do hiển thị | Nghĩa | Bạn làm gì |
|---|---|---|
| Lệch số tiết | Số tiết của môn ở hai lớp khác nhau trong tuần | Điền tay môn đó |
| Trùng ngày nghỉ | Môn có tiết rơi vào ngày nghỉ (ở lớp nguồn hoặc lớp bạn) | Điền tay, sắp xếp bài theo lịch bù |
| Nguồn chưa có tên bài | File nguồn để trống tên bài ở một tiết của môn | Kiểm tra file nguồn, điền tay |
| Chỉ có ở một file | Môn chỉ xuất hiện ở một trong hai file | Kiểm tra tên môn / thời khóa biểu |

Ngày nghỉ được nhận ra khi cả buổi ở file nguồn không có tên bài hoặc có chữ **"Nghỉ"**.

## 5. Lưu ý

- Chỉ điền vào **sheet tuần còn trống**. Muốn làm lại một tuần: xóa sheet tuần đó trong file đích, copy lại từ MẪU.
- Có thể làm dần: dùng file kết quả lần trước làm file đích cho lần sau — các tuần đã điền sẽ tự bỏ qua.
- File tải lên chỉ dùng để xử lý và **tự xóa sau tối đa 60 phút** (hoặc khi bấm *Làm lượt mới* / *Đăng xuất*).
  Nếu thấy thông báo **"Phiên xử lý đã hết hạn"**, chỉ cần tải file lên lại.
- Mỗi file tối đa **5MB**.
