<template>
  <details class="card guide">
    <summary>Hướng dẫn chuẩn bị file đích (làm một lần cho mỗi tuần)</summary>
    <ol>
      <li>Mở file lịch báo giảng của lớp bạn bằng Excel.</li>
      <li>Chuột phải vào sheet <strong>MẪU</strong> → <em>Move or Copy</em> (Di chuyển hoặc Sao chép) → tích <em>Create a copy</em>.</li>
      <li>Đổi tên bản sao theo tuần, ví dụ <strong>TUẦN 12</strong>.</li>
      <li>Nếu tuần đó thời khóa biểu khác MẪU, sửa môn học trực tiếp trên sheet tuần.</li>
      <li>Lưu file (.xlsx) rồi tải lên ở bước 1.</li>
    </ol>
    <p class="muted">
      Hệ thống chỉ điền vào sheet tuần còn trống, không tạo hay xóa sheet và giữ nguyên định dạng.
      File gốc của bạn không bị thay đổi — kết quả là một file mới để tải về.
    </p>
  </details>
</template>

<style scoped>
.guide summary {
  cursor: pointer;
  font-weight: 600;
}
.guide ol {
  margin: 12px 0 8px;
  padding-left: 20px;
}
.guide p {
  margin: 0;
}
</style>
