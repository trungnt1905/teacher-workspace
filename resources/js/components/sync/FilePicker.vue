<script setup>
import { computed, ref } from 'vue'
import { AlertTriangle, FileSpreadsheet, Upload } from 'lucide-vue-next'
import { checkFile, formatSize } from '../../utils/timetable'

const props = defineProps({
  label: { type: String, required: true },
  tag: { type: String, default: '' },
  hint: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const file = defineModel({ type: Object, default: null })

const input = ref(null)
const dragging = ref(false)
const problem = computed(() => checkFile(file.value))

function pick(list) {
  if (!props.disabled && list?.length) file.value = list[0]
}

function onDrop(event) {
  dragging.value = false
  pick(event.dataTransfer?.files)
}
</script>

<template>
  <div class="picker" :class="{ dragging, filled: file && !problem, invalid: problem }"
       @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
    <div class="head">
      <span class="label">{{ label }}</span>
      <span v-if="tag" class="pill">{{ tag }}</span>
    </div>
    <p v-if="hint" class="muted small">{{ hint }}</p>

    <div v-if="file" class="file">
      <span class="icon-tile" :class="problem ? '' : 'green'"><FileSpreadsheet /></span>
      <span class="file-text">
        <span class="name" :title="file.name">{{ file.name }}</span>
        <span class="muted small">{{ formatSize(file.size) }}</span>
      </span>
      <button type="button" class="btn btn-secondary change" :disabled="disabled" @click="input.click()">Đổi file</button>
    </div>
    <button v-else type="button" class="drop" :disabled="disabled" @click="input.click()">
      <span class="icon-tile blue"><Upload /></span>
      <span><strong>Chọn file</strong> hoặc kéo thả vào đây</span>
      <span class="muted small">.xlsx · tối đa 5MB</span>
    </button>

    <p v-if="problem" class="callout error"><AlertTriangle /><span>{{ problem }}</span></p>

    <input ref="input" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
           hidden @change="pick($event.target.files); $event.target.value = ''" />
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  transition: border-color 0.15s, background 0.15s;
}
.picker.dragging {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.picker.filled {
  border-color: var(--color-success-border);
}
.picker.invalid {
  border-color: var(--color-danger-border);
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.label {
  font-weight: 600;
}
.drop {
  font: inherit;
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 22px 12px;
  border: 1.5px dashed var(--color-border-strong);
  border-radius: var(--radius);
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.drop:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.drop .icon-tile {
  margin-bottom: 4px;
}
.file {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: var(--color-surface-muted);
}
.file-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.change {
  min-height: 34px;
  padding: 0 12px;
  font-size: 0.875rem;
}
</style>
