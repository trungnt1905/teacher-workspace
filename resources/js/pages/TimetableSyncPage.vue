<script setup>
import { computed, onMounted } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'
import StepPreview from '../components/sync/StepPreview.vue'
import StepResult from '../components/sync/StepResult.vue'
import StepSelect from '../components/sync/StepSelect.vue'
import StepUpload from '../components/sync/StepUpload.vue'
import SyncHeader from '../components/sync/SyncHeader.vue'
import SyncSidebar from '../components/sync/SyncSidebar.vue'
import { errorText } from '../services/api'
import { useSyncStore } from '../stores/sync'

// Wizard state lives in the store, so leaving and coming back keeps the current job (§10.2).
const sync = useSyncStore()
onMounted(() => sync.restore())

const errorMessage = computed(() => {
  if (!sync.error) return ''
  return sync.status === 'job_expired'
    ? 'Phiên xử lý đã hết hạn hoặc máy chủ vừa khởi động lại. Vui lòng chọn và tải file lên lại.'
    : errorText(sync.error)
})
</script>

<template>
  <div class="sync-page">
    <SyncHeader />

    <div class="layout">
      <div class="main">
        <p v-if="errorMessage" class="callout error" role="alert"><AlertTriangle /><span>{{ errorMessage }}</span></p>

        <StepUpload v-if="sync.step === 1" />
        <StepSelect v-else-if="sync.step === 2" />
        <StepPreview v-else-if="sync.step === 3 && sync.analysis" />
        <StepResult v-else-if="sync.step === 4 && sync.result" />
      </div>

      <SyncSidebar />
    </div>
  </div>
</template>

<style scoped>
.sync-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}
.main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
@media (max-width: 960px) {
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
