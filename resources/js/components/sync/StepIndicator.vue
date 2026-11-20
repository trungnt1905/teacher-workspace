<script setup>
defineProps({ step: { type: Number, required: true } })

const steps = ['Tải file', 'Chọn tuần và môn', 'Xem trước', 'Kết quả']
</script>

<template>
  <ol class="steps" aria-label="Các bước">
    <li v-for="(name, i) in steps" :key="name" :class="{ done: i + 1 < step, current: i + 1 === step }"
        :aria-current="i + 1 === step ? 'step' : undefined">
      <span class="num">{{ i + 1 }}</span>
      <span class="name">{{ name }}</span>
    </li>
  </ol>
</template>

<style scoped>
.steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}
li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  min-width: 0;
}
.num {
  flex: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 0.875rem;
}
.current {
  color: var(--text);
  font-weight: 600;
}
.current .num {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.done .num {
  background: var(--success-bg);
  border-color: var(--success);
  color: var(--success);
}
/* Phones: only circles for other steps; the current step takes the remaining width. */
@media (max-width: 600px) {
  .steps {
    display: flex;
  }
  .name {
    display: none;
  }
  .current {
    flex: 1;
  }
  .current .name {
    display: inline;
  }
}
</style>
