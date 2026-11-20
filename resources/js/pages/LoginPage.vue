<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
    <form class="card" @submit.prevent="submit">
      <h1>Teacher Workspace</h1>
      <p class="muted">Đăng nhập để tiếp tục</p>
      <label>
        Email
        <input v-model="email" type="email" autocomplete="username" required autofocus />
      </label>
      <label>
        Mật khẩu
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>
      <p v-if="error" class="alert alert-error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="busy">{{ busy ? 'Đang đăng nhập…' : 'Đăng nhập' }}</button>
    </form>
  </main>
</template>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 16px;
}
.card {
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
h1 {
  margin: 0;
}
.muted {
  margin: -8px 0 4px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-weight: 500;
}
</style>
