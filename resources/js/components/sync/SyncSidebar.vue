<script setup>
import { computed } from 'vue'
import { Check, Clock, FileSpreadsheet, Info } from 'lucide-vue-next'
import { useSyncStore } from '../../stores/sync'
import { STEPS } from './steps'

const sync = useSyncStore()

const expires = computed(() => {
  if (!sync.job?.expires_at) return ''
  return new Date(sync.job.expires_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
})

function state(step) {
  if (step.number < sync.step || (step.number === 4 && sync.status === 'completed')) return 'done'
  return step.number === sync.step ? 'current' : 'todo'
}
</script>

<template>
  <aside class="sidebar">
    <section class="card block">
      <h3>Tiến trình</h3>
      <ol class="steps">
        <li v-for="step in STEPS" :key="step.number" :class="state(step)"
            :aria-current="state(step) === 'current' ? 'step' : undefined">
          <span class="dot">
            <Check v-if="state(step) === 'done'" />
            <template v-else>{{ step.number }}</template>
          </span>
          <span class="text">
            <span class="name">{{ step.name }}</span>
            <span class="muted small">{{ step.description }}</span>
          </span>
        </li>
      </ol>
    </section>

    <section v-if="sync.job" class="card block">
      <h3>Phiên làm việc</h3>
      <dl class="facts">
        <div>
          <dt><FileSpreadsheet /> File nguồn</dt>
          <dd :title="sync.job.source_file_name">{{ sync.job.source_file_name }}</dd>
        </div>
        <div>
          <dt><FileSpreadsheet /> File đích</dt>
          <dd :title="sync.job.target_file_name">{{ sync.job.target_file_name }}</dd>
        </div>
        <div class="row">
          <dt>Tuần đã chọn</dt>
          <dd><strong>{{ sync.selectedWeeks.length }}</strong>/{{ sync.selectableWeeks.length }} sẵn sàng</dd>
        </div>
        <div class="row">
          <dt>Môn đồng bộ</dt>
          <dd><strong>{{ sync.selectedSubjects.length }}</strong>/{{ sync.job.subjects.length }}</dd>
        </div>
      </dl>
      <p v-if="expires" class="expires small"><Clock /> File trên máy chủ tự xóa lúc {{ expires }}</p>
    </section>

    <details class="card block guide" :open="sync.step === 1">
      <summary><Info /> Chuẩn bị file đích</summary>
      <ol>
        <li>Mỗi tuần một file: copy file mẫu <strong>MAU_LBG</strong> (đã có thời khóa biểu lớp bạn) thành file mới.</li>
        <li>Không cần đổi tên sheet hay sửa ngày tháng — ở bước 2 bạn chọn tuần, hệ thống điền tiêu đề, ngày và tên bài theo file nguồn.</li>
        <li>Nếu tuần đó thời khóa biểu khác, sửa cột Môn ngay trên sheet.</li>
        <li>Lưu file (.xlsx) rồi tải lên cùng file nguồn (file nguồn có thể chứa nhiều tuần).</li>
        <li>File có nhiều sheet “TUẦN n” vẫn dùng được: tuần nào có sheet thì điền vào sheet đó.</li>
      </ol>
      <p class="muted small">
        Hệ thống chỉ điền vào sheet tuần còn trống, giữ nguyên định dạng. File gốc không bị thay đổi — kết quả là một file mới.
        File cũ (bảng lệch dòng so với mẫu) vẫn đọc được: hệ thống tự tìm bảng theo nội dung.
      </p>
    </details>
  </aside>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.block {
  padding: 18px 20px;
}
.block h3 {
  margin-bottom: 14px;
}
.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.steps li {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}
.steps li.current {
  background: var(--color-primary-soft);
}
.dot {
  flex: none;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 0.8125rem;
  font-weight: 600;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
}
.dot svg {
  width: 16px;
  height: 16px;
}
.current .dot {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}
.done .dot {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-muted);
  color: var(--color-primary);
}
.text {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}
.name {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
.todo .name {
  color: var(--color-text-muted);
  font-weight: 500;
}
.facts {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.facts dt {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 500;
}
.facts dt svg {
  width: 14px;
  height: 14px;
}
.facts dd {
  margin: 2px 0 0;
  font-size: 0.875rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.facts .row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-top: 10px;
  border-top: 1px dashed var(--color-border);
}
.facts .row dd {
  margin: 0;
  font-weight: 400;
}
.expires {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}
.expires svg {
  width: 14px;
  height: 14px;
}
.guide summary {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9375rem;
  list-style: none;
}
.guide summary::-webkit-details-marker {
  display: none;
}
.guide summary svg {
  width: 18px;
  height: 18px;
  color: var(--color-primary);
}
.guide ol {
  margin: 12px 0 10px;
  padding-left: 18px;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
