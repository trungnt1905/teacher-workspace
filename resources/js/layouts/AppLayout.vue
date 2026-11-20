<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSyncStore } from '../stores/sync'
import { useUiStore } from '../stores/ui'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

async function logout() {
  await useSyncStore().startOver() // delete the uploaded files on the server too
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">Teacher Workspace</RouterLink>
      <nav class="nav">
        <RouterLink to="/" exact-active-class="active">Tổng quan</RouterLink>
        <RouterLink to="/lich-bao-giang" active-class="active">Lịch báo giảng</RouterLink>
      </nav>
      <div class="account">
        <span class="email" :title="auth.user?.email">{{ auth.user?.email }}</span>
        <button type="button" class="link" @click="logout">Đăng xuất</button>
      </div>
    </header>
    <p v-if="ui.serverWaking" class="waking" role="status">Đang khởi động máy chủ, vui lòng chờ…</p>
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
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 24px;
  padding: 12px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.brand {
  font-weight: 700;
  color: var(--text);
  text-decoration: none;
}
.nav {
  display: flex;
  gap: 16px;
}
.nav a {
  color: var(--muted);
  text-decoration: none;
}
.nav a.active {
  color: var(--primary);
  font-weight: 600;
}
.account {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.email {
  color: var(--muted);
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}
.waking {
  margin: 0;
  padding: 8px 16px;
  background: var(--warn-bg);
  color: var(--warn);
  text-align: center;
}
.content {
  flex: 1;
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}
</style>
