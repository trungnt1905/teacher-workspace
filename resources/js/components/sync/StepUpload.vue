<script setup>
import { computed, ref } from 'vue'
import { ChevronRight, Loader2, ShieldCheck } from 'lucide-vue-next'
import { useSyncStore } from '../../stores/sync'
import { checkFile } from '../../utils/timetable'
import FilePicker from './FilePicker.vue'
import AppPanel from '../ui/AppPanel.vue'

const sync = useSyncStore()
const source = ref(null)
const target = ref(null)

const ready = computed(() => source.value && target.value && !checkFile(source.value) && !checkFile(target.value))
const uploading = computed(() => sync.status === 'uploading')
const chosen = computed(() => [source.value, target.value].filter(Boolean).length)
</script>

<template>
  <AppPanel eyebrow="Bước 1 · Tải file" title="Chọn hai file lịch báo giảng"
             description="File nguồn cung cấp tên bài và đồ dùng; file đích quyết định thời khóa biểu và định dạng.">
    <div class="pickers">
      <FilePicker v-model="source" label="File nguồn" tag="Lớp khác" :disabled="uploading"
                  hint="Lịch báo giảng đã có tên bài, đồ dùng dạy học." />
      <FilePicker v-model="target" label="File đích" tag="Lớp của bạn" :disabled="uploading"
                  hint="Lịch báo giảng lớp bạn — sheet tuần (ví dụ TUẦN 12) còn trống. Tuần nào có trong file này thì xử lý tuần đó." />
    </div>

    <div v-if="uploading" class="uploading">
      <div class="progress-labels small">
        <span>{{ sync.uploadProgress < 100 ? 'Đang tải lên…' : 'Đang đọc file…' }}</span>
        <span class="muted">{{ sync.uploadProgress }}%</span>
      </div>
      <div class="progress-track" role="progressbar" :aria-valuenow="sync.uploadProgress" aria-valuemin="0" aria-valuemax="100">
        <div class="progress-fill" :style="{ width: `${sync.uploadProgress}%` }"></div>
      </div>
    </div>

    <template #footer>
      <span class="muted small note"><ShieldCheck /> File chỉ dùng để xử lý, tự xóa sau tối đa 60 phút</span>
      <span class="muted small">{{ chosen }}/2 file đã chọn</span>
      <button type="button" class="btn btn-primary" :disabled="!ready || uploading" @click="sync.upload(source, target)">
        <Loader2 v-if="uploading" class="spin" />
        {{ uploading ? 'Đang xử lý…' : 'Tải lên và đọc file' }}
        <ChevronRight v-if="!uploading" />
      </button>
    </template>
  </AppPanel>
</template>

<style scoped>
.pickers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
  gap: 16px;
}
.uploading {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.progress-labels {
  display: flex;
  justify-content: space-between;
}
.note {
  display: flex;
  align-items: center;
  gap: 6px;
}
.note svg {
  width: 16px;
  height: 16px;
  color: var(--color-success);
}
</style>
