<script setup>
/**
 * Top card of a feature screen (docs/design-system.md): icon tile + title + optional badge + subtitle,
 * and a right-hand area (default slot) for progress, timers or actions.
 */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  badge: { type: String, default: '' },
})
</script>

<template>
  <header class="card page-header">
    <div class="ident">
      <span class="icon-tile"><slot name="icon" /></span>
      <div class="titles">
        <div class="title-row">
          <h1>{{ title }}</h1>
          <span v-if="badge" class="pill">{{ badge }}</span>
        </div>
        <p v-if="subtitle" class="muted small sub" :title="subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <slot />
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4) var(--space-8);
  padding: var(--space-4) var(--space-5);
}
.ident {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex: 1 1 320px;
}
.titles {
  min-width: 0;
}
.title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) 10px;
}
.title-row h1 {
  font-size: var(--text-lg);
}
.sub {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
