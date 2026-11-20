<script setup>
import { ArrowRight, CalendarDays, FileSpreadsheet, ListChecks } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
</script>

<template>
  <section class="dashboard">
    <header class="hello">
      <p class="eyebrow">Tổng quan</p>
      <h1>Xin chào{{ auth.user?.email ? `, ${auth.user.email.split('@')[0]}` : '' }}</h1>
      <p class="muted">Chọn công việc bạn muốn làm hôm nay.</p>
    </header>

    <div class="grid">
      <RouterLink to="/lich-bao-giang" class="card feature">
        <span class="icon-tile blue"><CalendarDays /></span>
        <div class="feature-body">
          <div class="feature-title">
            <h2>Đồng bộ lịch báo giảng</h2>
            <span class="pill green">Sẵn sàng</span>
          </div>
          <p class="muted">
            Lấy tên bài và đồ dùng dạy học từ lịch báo giảng của lớp khác, điền vào lịch của lớp bạn theo thời khóa biểu
            riêng — giữ nguyên định dạng file Excel.
          </p>
          <ul class="facts">
            <li><FileSpreadsheet /> 2 file .xlsx</li>
            <li><ListChecks /> Xem trước trước khi tạo file</li>
          </ul>
        </div>
        <ArrowRight class="go" />
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.hello {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 520px), 1fr));
  gap: 16px;
}
.feature {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 22px;
  color: inherit;
  text-decoration: none;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.feature:hover {
  border-color: var(--color-primary-border);
  box-shadow: var(--shadow-hover);
  transform: translateY(-1px);
}
.feature-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.feature-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}
.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}
.facts li {
  display: flex;
  align-items: center;
  gap: 6px;
}
.facts svg {
  width: 16px;
  height: 16px;
  color: var(--color-text-muted);
}
.go {
  flex: none;
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
  margin-top: 10px;
}
.feature:hover .go {
  color: var(--color-primary);
}
</style>
