<template>
  <div class="auth-page">
    <div class="auth-card glass-card">
      <h1 class="auth-title">注册</h1>
      <p class="auth-sub">创建账号，开启你的开源之旅</p>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="input-field"
            placeholder="3-32 位字母数字下划线"
            required
            autocomplete="username"
            pattern="^[a-zA-Z0-9_]{3,32}$"
            :class="{ 'input-error': fieldError.username }"
          />
          <span v-if="fieldError.username" class="field-error">{{ fieldError.username }}</span>
        </div>

        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="input-field"
            placeholder="you@example.com"
            required
            autocomplete="email"
            :class="{ 'input-error': fieldError.email }"
          />
          <span v-if="fieldError.email" class="field-error">{{ fieldError.email }}</span>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="input-field"
            placeholder="至少 8 位"
            required
            autocomplete="new-password"
            minlength="8"
            :class="{ 'input-error': fieldError.password }"
          />
          <span v-if="fieldError.password" class="field-error">{{ fieldError.password }}</span>
        </div>

        <Transition name="fade">
          <p v-if="generalError" class="error-msg">{{ generalError }}</p>
        </Transition>

        <button type="submit" class="btn btn-primary auth-submit" :disabled="loading">
          <span v-if="!loading">创建账号</span>
          <span v-else class="spinner"></span>
        </button>
      </form>

      <p class="auth-switch">
        已有账号？<router-link :to="{ name: 'Login' }">直接登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ username: '', email: '', password: '' })
const fieldError = reactive({ username: '', email: '', password: '' })
const generalError = ref('')
const loading = ref(false)

function validate() {
  fieldError.username = ''
  fieldError.email = ''
  fieldError.password = ''

  if (!/^[a-zA-Z0-9_]{3,32}$/.test(form.username)) {
    fieldError.username = '用户名必须为 3-32 位字母、数字或下划线'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    fieldError.email = '邮箱格式不正确'
  }
  if (form.password.length < 8) {
    fieldError.password = '密码至少 8 位'
  }

  return !fieldError.username && !fieldError.email && !fieldError.password
}

async function handleSubmit() {
  generalError.value = ''
  if (!validate()) return

  loading.value = true
  try {
    await auth.registerUser(form.username, form.email, form.password)
    router.push('/')
  } catch (e) {
    generalError.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
  padding: var(--space-6);
}
.auth-card {
  width: 100%;
  max-width: 420px;
  padding: var(--space-10);
}
.auth-title {
  font-size: 2rem;
  margin-bottom: var(--space-2);
  text-align: center;
}
.auth-sub {
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: var(--space-8);
  font-size: 0.9rem;
}
.auth-form { display: flex; flex-direction: column; gap: var(--space-5); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); }
.form-group label { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
.auth-submit { margin-top: var(--space-2); width: 100%; }
.input-error { border-color: var(--neon-coral) !important; }
.field-error { font-size: 0.78rem; color: var(--neon-coral); }
.error-msg {
  color: var(--neon-coral);
  font-size: 0.85rem;
  text-align: center;
  padding: var(--space-3);
  background: rgba(255, 82, 82, 0.08);
  border: 1px solid rgba(255, 82, 82, 0.2);
  border-radius: var(--radius-sm);
}
.auth-switch {
  text-align: center;
  margin-top: var(--space-6);
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.spinner {
  display: inline-block;
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
