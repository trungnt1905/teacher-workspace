<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpenCheck, Loader2, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '../stores/auth'
import { useSyncStore } from '../stores/sync'
import { useUiStore } from '../stores/ui'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

const initial = computed(() => (auth.user?.email ?? '?').charAt(0).toUpperCase())

async function logout() {
  await useSyncStore().startOver() // delete the uploaded files on the server too
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/" class="brand">
          <span class="icon-tile brand-tile"><BookOpenCheck /></span>
          <span class="brand-text">
            <strong>Teacher Workspace</strong>
            <span class="muted small">Trợ lý công việc giáo viên</span>
          </span>
        </RouterLink>

        <nav class="nav" aria-label="Chức năng">
          <RouterLink to="/" exact-active-class="active">Tổng quan</RouterLink>
          <RouterLink to="/lich-bao-giang" active-class="active">Lịch báo giảng</RouterLink>
        </nav>

        <div class="account">
          <span class="avatar" aria-hidden="true">{{ initial }}</span>
          <span class="email" :title="auth.user?.email">{{ auth.user?.email }}</span>
          <button type="button" class="btn btn-ghost" title="Đăng xuất" @click="logout">
            <LogOut /><span class="logout-text">Đăng xuất</span>
          </button>
        </div>
      </div>
    </header>

    <div v-if="ui.serverWaking" class="waking" role="status">
      <Loader2 class="spin" /> Đang khởi động máy chủ, vui lòng chờ…
    </div>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-topbar);
  backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--color-border);
}
.topbar-inner {
  max-width: 1240px;
  margin: 0 auto;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  gap: 12px 32px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text);
  text-decoration: none;
}
.brand-tile {
  width: 40px;
  height: 40px;
}
.brand-tile svg {
  width: 20px;
  height: 20px;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}
.nav {
  display: flex;
  gap: 4px;
}
.nav a {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-weight: 500;
  text-decoration: none;
}
.nav a:hover {
  background: var(--color-surface-sunken);
  color: var(--color-text);
}
.nav a.active {
  background: var(--color-primary-soft);
  color: var(--color-primary-strong);
  font-weight: 600;
}
.account {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.avatar {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--color-primary-soft);
  color: var(--color-primary-strong);
  font-weight: 700;
  font-size: 0.875rem;
}
.email {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}
.waking {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--color-warning-soft);
  border-bottom: 1px solid var(--color-warning-border);
  color: var(--color-warning-strong);
  font-size: 0.875rem;
  font-weight: 500;
}
.waking svg {
  width: 16px;
  height: 16px;
}
.content {
  flex: 1;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 24px 56px;
}

</style>
