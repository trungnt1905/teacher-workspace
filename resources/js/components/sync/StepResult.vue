<script setup>
import { computed, ref } from 'vue'
import { downloadUrl } from '../../services/timetable'
import { useSyncStore } from '../../stores/sync'
import { groupTodo, todoText } from '../../utils/timetable'

const sync = useSyncStore()
const result = computed(() => sync.result)
const groups = computed(() => groupTodo(result.value?.manual_todo))
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
  <section class="step">
    <div class="card done">
      <p class="alert alert-ok">
        Đã tạo file: điền {{ result.weeks_filled.length }} tuần
        ({{ result.weeks_filled.map((w) => `Tuần ${w}`).join(', ') }}), {{ result.cells_written }} ô.
      </p>
      <div class="download">
        <a class="button" :href="downloadUrl(sync.job.job_id)" :download="result.file_name">Tải file Excel</a>
        <span class="muted name">{{ result.file_name }}</span>
      </div>
      <p class="muted small">
        File được giữ trên máy chủ khoảng 60 phút rồi tự xóa. Hãy tải về ngay; file gốc của bạn không bị thay đổi.
      </p>
    </div>

    <div v-if="groups.length" class="card todo">
      <div class="head">
        <h2>Việc cần làm thủ công</h2>
        <div class="tools">
          <button type="button" class="link" @click="copyTodo">{{ copied ? 'Đã sao chép' : 'Sao chép' }}</button>
          <button type="button" class="link" @click="printPage">In</button>
        </div>
      </div>
      <p class="muted small">Các môn dưới đây không được điền tự động. Mở file kết quả và điền tay.</p>
      <section v-for="g in groups" :key="g.week">
        <h3>Tuần {{ g.week }}</h3>
        <ul>
          <li v-for="m in g.messages" :key="m">{{ m }}</li>
        </ul>
      </section>
    </div>
    <p v-else class="alert alert-ok">Không có môn nào cần điền thủ công.</p>

    <div class="actions">
      <button type="button" class="secondary" @click="sync.backToSelection()">Quay lại chọn tuần/môn</button>
      <button type="button" @click="sync.startOver()">Làm lượt mới</button>
    </div>
  </section>
</template>

<style scoped>
.step {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.done {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.download {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.name {
  overflow-wrap: anywhere;
}
.small {
  margin: 0;
  font-size: 0.875rem;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.tools {
  display: flex;
  gap: 16px;
}
.todo ul {
  margin: 4px 0 12px;
  padding-left: 20px;
}
.todo h3 {
  margin-top: 8px;
}
@media print {
  .download,
  .actions,
  .tools {
    display: none;
  }
}
</style>
