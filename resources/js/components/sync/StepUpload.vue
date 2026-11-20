<script setup>
import { computed, ref } from 'vue'
import { useSyncStore } from '../../stores/sync'
import { checkFile } from '../../utils/timetable'
import FilePicker from './FilePicker.vue'

const sync = useSyncStore()
const source = ref(null)
const target = ref(null)

const ready = computed(() => source.value && target.value && !checkFile(source.value) && !checkFile(target.value))
const uploading = computed(() => sync.status === 'uploading')
</script>

<template>
  <section class="step">
    <div class="pickers">
      <FilePicker v-model="source" label="File nguồn" hint="Lịch báo giảng của lớp khác, đã có tên bài." :disabled="uploading" />
      <FilePicker v-model="target" label="File đích" hint="Lịch báo giảng của lớp bạn. Cần có sẵn các sheet tuần copy từ MẪU."
                  :disabled="uploading" />
    </div>

    <p class="muted note">Chỉ hỗ trợ file .xlsx, tối đa 5MB mỗi file.</p>

    <div v-if="uploading" class="progress" role="progressbar" :aria-valuenow="sync.uploadProgress" aria-valuemin="0" aria-valuemax="100">
      <div class="bar" :style="{ width: `${sync.uploadProgress}%` }"></div>
      <span>{{ sync.uploadProgress < 100 ? `Đang tải lên… ${sync.uploadProgress}%` : 'Đang đọc file…' }}</span>
    </div>

    <div class="actions">
      <span></span>
      <button type="button" :disabled="!ready || uploading" @click="sync.upload(source, target)">
        {{ uploading ? 'Đang xử lý…' : 'Tải lên và đọc file' }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.step {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.pickers {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.note {
  margin: 0;
}
.progress {
  position: relative;
  height: 32px;
  border-radius: 6px;
  background: var(--surface-muted);
  overflow: hidden;
  display: grid;
  place-items: center;
}
.progress .bar {
  position: absolute;
  inset: 0 auto 0 0;
  background: var(--primary-bg);
  transition: width 0.2s;
}
.progress span {
  position: relative;
  font-size: 0.875rem;
}
</style>
