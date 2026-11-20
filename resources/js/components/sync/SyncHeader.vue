<script setup>
import { computed } from 'vue'
import { FileSpreadsheet, RotateCcw } from 'lucide-vue-next'
import { useSyncStore } from '../../stores/sync'
import PageHeader from '../ui/PageHeader.vue'
import { STEPS } from './steps'

const sync = useSyncStore()

const current = computed(() => STEPS[sync.step - 1])
// Progress counts finished steps; the last step is "done" once the file exists.
const percent = computed(() => (sync.status === 'completed' ? 100 : Math.round(((sync.step - 1) / STEPS.length) * 100)))
const subtitle = computed(() =>
  sync.job
    ? `${sync.job.source_file_name} → ${sync.job.target_file_name}`
    : 'Lấy tên bài và đồ dùng từ lịch của lớp khác, điền theo thời khóa biểu lớp bạn',
)
</script>

<template>
  <PageHeader title="Đồng bộ lịch báo giảng" badge="4 bước" :subtitle="subtitle">
    <template #icon><FileSpreadsheet /></template>

    <div class="progress">
      <div class="progress-labels">
        <span class="muted small">Tiến độ</span>
        <span class="small"><strong>Bước {{ sync.step }}/{{ STEPS.length }}</strong> · {{ current.name }}</span>
      </div>
      <div class="progress-track"><div class="progress-fill" :style="{ width: `${percent}%` }"></div></div>
    </div>

    <button v-if="sync.job" type="button" class="btn btn-secondary" :disabled="sync.busy" @click="sync.startOver()">
      <RotateCcw /> Làm lượt mới
    </button>
  </PageHeader>
</template>

<style scoped>
.progress {
  flex: 1 1 260px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.progress-labels {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
}
</style>
