<template>
  <div class="auth-page">
    <div class="auth-card glass-card">
      <h1 class="auth-title">登录</h1>
      <p class="auth-sub">欢迎回来，继续你的项目探索</p>

      <form @submit.prevent="handleSubmit" class="auth-form">
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
          />
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
            autocomplete="current-password"
            minlength="8"
          />
        </div>

        <Transition name="fade">
          <p v-if="error" class="error-msg">{{ error }}</p>
        </Transition>

        <button type="submit" class="btn btn-primary auth-submit" :disabled="loading">
          <span v-if="!loading">登录</span>
          <span v-else class="spinner"></span>
        </button>
      </form>

      <p class="auth-switch">
        还没账号？<router-link :to="{ name: 'Register' }">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || '登录失败'
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
