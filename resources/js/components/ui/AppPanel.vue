<script setup>
/**
 * Standard content card for every screen (docs/design-system.md):
 * eyebrow + title (+ description), optional #aside (pills/actions on the right),
 * body (default slot) and an optional #footer action bar (back on the left, main action on the right).
 */
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <section class="card panel">
    <header class="panel-head">
      <div class="titles">
        <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
        <h2>{{ title }}</h2>
        <p v-if="description" class="muted desc">{{ description }}</p>
      </div>
      <div v-if="$slots.aside" class="aside"><slot name="aside" /></div>
    </header>

    <div class="panel-body"><slot /></div>

    <footer v-if="$slots.footer" class="panel-foot"><slot name="footer" /></footer>
  </section>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
}
.panel-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  padding: 22px var(--space-6) 0;
}
.titles {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.desc {
  font-size: var(--text-base);
}
.aside {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.panel-body {
  padding: var(--space-5) var(--space-6) var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.panel-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
}
</style>
