<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, BookOpenCheck, Loader2 } from 'lucide-vue-next'
import { apiError, errorText } from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')

async function submit() {
  busy.value = true
  error.value = ''
  try {
    await auth.login(email.value.trim(), password.value)
    const target = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') ? route.query.redirect : '/'
    router.replace(target)
  } catch (e) {
    error.value = errorText(apiError(e))
    password.value = ''
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="login">
    <form class="card login-card" @submit.prevent="submit">
      <div class="head">
        <span class="icon-tile blue"><BookOpenCheck /></span>
        <div>
          <h1>Teacher Workspace</h1>
          <p class="muted">Đăng nhập để tiếp tục</p>
        </div>
      </div>

      <label class="field">
        Email
        <input v-model="email" class="input" type="email" autocomplete="username" placeholder="ten@example.com" required autofocus />
      </label>
      <label class="field">
        Mật khẩu
        <input v-model="password" class="input" type="password" autocomplete="current-password" placeholder="••••••••••" required />
      </label>

      <p v-if="error" class="callout error" role="alert"><AlertTriangle />{{ error }}</p>

      <button type="submit" class="btn btn-primary btn-lg" :disabled="busy">
        <Loader2 v-if="busy" class="spin" />
        {{ busy ? 'Đang đăng nhập…' : 'Đăng nhập' }}
      </button>
    </form>
    <p class="muted small foot">Hệ thống dành cho giáo viên · Dữ liệu tải lên được xóa sau khi xử lý</p>
  </main>
</template>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px 16px;
  background:
    radial-gradient(circle at 20% 0%, var(--color-primary-soft), transparent 45%),
    radial-gradient(circle at 100% 100%, var(--color-action-soft), transparent 40%),
    var(--color-bg);
}
.login-card {
  width: 100%;
  max-width: 400px;
  padding: 32px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 4px;
}
.head h1 {
  font-size: 1.25rem;
}
.foot {
  text-align: center;
}
</style>
