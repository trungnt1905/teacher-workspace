<script setup>
import { computed, ref } from 'vue'
import { Check, CheckCircle2, ChevronLeft, Copy, Download, FileSpreadsheet, Flag, Printer, RotateCcw } from 'lucide-vue-next'
import { downloadUrl } from '../../services/timetable'
import { useSyncStore } from '../../stores/sync'
import { groupTodo, todoText } from '../../utils/timetable'
import AppPanel from '../ui/AppPanel.vue'

const sync = useSyncStore()
const result = computed(() => sync.result)
const groups = computed(() => groupTodo(result.value?.manual_todo))
const todoCount = computed(() => result.value?.manual_todo?.length ?? 0)
const copied = ref(false)

function printPage() {
  window.print()
}

async function copyTodo() {
  try {
    await navigator.clipboard.writeText(todoText(result.value.manual_todo))
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <AppPanel eyebrow="Bước 4 · Kết quả" title="File đã sẵn sàng">
    <div class="hero">
      <span class="hero-icon"><CheckCircle2 /></span>
      <div class="hero-text">
        <h3>Đã tạo file thành công</h3>
        <p class="muted small">File gốc của bạn không bị thay đổi. File kết quả được giữ trên máy chủ khoảng 60 phút — hãy tải về ngay.</p>
      </div>
    </div>

    <div class="stats">
      <div class="stat">
        <span class="stat-value">{{ result.weeks_filled.length }}</span>
        <span class="muted small">Tuần đã điền</span>
      </div>
      <div class="stat">
        <span class="stat-value">{{ result.cells_written }}</span>
        <span class="muted small">Ô đã ghi</span>
      </div>
      <div class="stat" :class="{ amber: todoCount }">
        <span class="stat-value">{{ todoCount }}</span>
        <span class="muted small">Việc cần điền tay</span>
      </div>
    </div>

    <div class="download">
      <span class="icon-tile green"><FileSpreadsheet /></span>
      <span class="dl-text">
        <span class="dl-name" :title="result.file_name">{{ result.file_name }}</span>
        <span class="muted small">{{ result.weeks_filled.map((w) => `Tuần ${w}`).join(', ') }}</span>
      </span>
      <a class="btn btn-primary btn-lg" :href="downloadUrl(sync.job.job_id)" :download="result.file_name">
        <Download /> Tải file Excel
      </a>
    </div>

    <section v-if="groups.length" class="todo">
      <div class="todo-head">
        <h3><Flag /> Việc cần làm thủ công</h3>
        <div class="tools">
          <button type="button" class="btn btn-ghost" @click="copyTodo">
            <Check v-if="copied" /><Copy v-else /> {{ copied ? 'Đã sao chép' : 'Sao chép' }}
          </button>
          <button type="button" class="btn btn-ghost" @click="printPage"><Printer /> In</button>
        </div>
      </div>
      <p class="muted small">Các môn dưới đây không được điền tự động. Mở file kết quả và điền tay.</p>
      <div v-for="g in groups" :key="g.week" class="todo-week">
        <span class="pill amber">Tuần {{ g.week }}</span>
        <ul>
          <li v-for="m in g.messages" :key="m">{{ m }}</li>
        </ul>
      </div>
    </section>
    <p v-else class="callout success"><CheckCircle2 /><span>Không có môn nào cần điền thủ công.</span></p>

    <template #footer>
      <button type="button" class="btn btn-secondary" @click="sync.backToSelection()"><ChevronLeft /> Chọn lại tuần/môn</button>
      <button type="button" class="btn btn-secondary" @click="sync.startOver()"><RotateCcw /> Làm lượt mới</button>
    </template>
  </AppPanel>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--color-success-soft), var(--color-success-surface));
  border: 1px solid var(--color-success-border);
}
.hero-icon {
  flex: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-success);
  color: var(--color-text-inverse);
}
.hero-icon svg {
  width: 26px;
  height: 26px;
}
.hero-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.stat {
  display: flex;
  flex-direction: column;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-muted);
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}
.stat.amber {
  background: var(--color-warning-soft);
  border-color: var(--color-warning-border);
}
.stat.amber .stat-value {
  color: var(--color-warning-strong);
}
.download {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}
.dl-text {
  flex: 1;
  min-width: 180px;
  display: flex;
  flex-direction: column;
}
.dl-name {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.todo {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--color-warning-border);
  border-radius: var(--radius);
  background: var(--color-warning-surface);
}
.todo-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.todo-head h3 {
  display: flex;
  align-items: center;
  gap: 8px;
}
.todo-head h3 svg {
  width: 18px;
  height: 18px;
  color: var(--color-warning);
}
.tools {
  display: flex;
  gap: 4px;
}
.todo-week {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}
.todo-week ul {
  margin: 0;
  padding-left: 20px;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
@media print {
  .download,
  .tools,
  .stats {
    display: none;
  }
}
</style>
