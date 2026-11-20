<template>
  <section>
    <h1>Tổng quan</h1>
    <RouterLink to="/lich-bao-giang" class="card feature">
      <h2>Lịch báo giảng</h2>
      <p>Lấy tên bài và đồ dùng dạy học từ lịch báo giảng của lớp khác, điền vào lịch báo giảng của lớp bạn theo thời khóa biểu riêng.</p>
    </RouterLink>
  </section>
</template>

<style scoped>
.feature {
  display: block;
  margin-top: 16px;
  color: inherit;
  text-decoration: none;
}
.feature:hover {
  border-color: var(--primary);
}
.feature p {
  color: var(--muted);
  margin: 4px 0 0;
}
</style>
