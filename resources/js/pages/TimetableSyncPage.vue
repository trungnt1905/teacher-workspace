<script setup>
import { computed, onMounted } from 'vue'
import StepIndicator from '../components/sync/StepIndicator.vue'
import StepPreview from '../components/sync/StepPreview.vue'
import StepResult from '../components/sync/StepResult.vue'
import StepSelect from '../components/sync/StepSelect.vue'
import StepUpload from '../components/sync/StepUpload.vue'
import SyncGuide from '../components/sync/SyncGuide.vue'
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
  <section class="page">
    <h1>Đồng bộ lịch báo giảng</h1>
    <SyncGuide />
    <StepIndicator :step="sync.step" />

    <p v-if="errorMessage" class="alert alert-error" role="alert">{{ errorMessage }}</p>

    <StepUpload v-if="sync.step === 1" />
    <StepSelect v-else-if="sync.step === 2" />
    <StepPreview v-else-if="sync.step === 3 && sync.analysis" />
    <StepResult v-else-if="sync.step === 4 && sync.result" />
  </section>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
h1 {
  margin: 0;
}
</style>
