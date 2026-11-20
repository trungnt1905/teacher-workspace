<script setup>
import { computed, ref } from 'vue'
import { checkFile, formatSize } from '../../utils/timetable'

const props = defineProps({
  label: { type: String, required: true },
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
  <div class="picker" :class="{ dragging, filled: file, invalid: problem }"
       @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
    <div class="head">
      <strong>{{ label }}</strong>
      <span v-if="hint" class="muted">{{ hint }}</span>
    </div>

    <div v-if="file" class="file">
      <span class="name" :title="file.name">{{ file.name }}</span>
      <span class="muted">{{ formatSize(file.size) }}</span>
      <button type="button" class="secondary" :disabled="disabled" @click="input.click()">Đổi file</button>
    </div>
    <button v-else type="button" class="secondary choose" :disabled="disabled" @click="input.click()">
      Chọn file .xlsx hoặc kéo thả vào đây
    </button>

    <p v-if="problem" class="alert alert-error">{{ problem }}</p>

    <input ref="input" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
           hidden @change="pick($event.target.files); $event.target.value = ''" />
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  border: 2px dashed var(--border);
  border-radius: 8px;
  background: var(--surface);
}
.picker.dragging {
  border-color: var(--primary);
  background: var(--primary-bg);
}
.picker.filled {
  border-style: solid;
}
.picker.invalid {
  border-color: var(--danger);
}
.head {
  display: flex;
  flex-direction: column;
}
.head .muted {
  font-size: 0.875rem;
}
.file {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.name {
  font-weight: 500;
  overflow-wrap: anywhere;
}
.choose {
  padding: 16px;
}
</style>
