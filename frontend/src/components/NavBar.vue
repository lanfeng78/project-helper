<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="logo">
        <div class="logo-mark">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.3"/>
            <rect x="14" y="3" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.6"/>
            <rect x="3" y="14" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.8"/>
            <rect x="14" y="14" width="7" height="7" rx="1.5" fill="currentColor"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">[ project_helper ]</span>
          <span class="logo-sub">AI · code · cartographer</span>
        </div>
      </router-link>
      <div class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          Home
        </router-link>
        <a href="https://github.com/lanfeng78/project-helper" target="_blank" rel="noopener noreferrer" class="nav-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
          GitHub
        </a>

        <template v-if="auth.user">
          <div class="user-chip">
            <span class="user-avatar">{{ auth.user.username.charAt(0).toUpperCase() }}</span>
            <span class="user-name">{{ auth.user.username }}</span>
          </div>
          <button class="nav-link nav-link-btn" @click="handleLogout">登出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="nav-link" exact-active-class="active">登录</router-link>
          <router-link to="/register" class="nav-link nav-link-cta" exact-active-class="active">注册</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10, 8, 34, 0.72);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-bottom: 1px solid var(--border-subtle);
  box-shadow: 0 1px 0 0 rgba(0, 229, 255, 0.06);
}

.nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--space-6);
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo { display: flex; align-items: center; gap: 12px; text-decoration: none; }
.logo-mark { color: var(--neon-cyan); }
.logo-text { display: flex; flex-direction: column; }
.logo-name {
  font-size: 0.95rem;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text-primary);
  letter-spacing: 0.02em;
}
.logo-sub {
  font-size: 0.62rem;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.nav-links { display: flex; align-items: center; gap: var(--space-2); }

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all var(--duration-fast);
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
}
.nav-link:hover { color: var(--text-primary); background: rgba(255,255,255,0.04); }
.nav-link.active { color: var(--neon-cyan); background: var(--neon-cyan-10); }
.nav-link-cta {
  background: var(--gradient-btn);
  color: #fff !important;
  font-weight: 600;
}
.nav-link-cta:hover { box-shadow: 0 0 16px rgba(0, 229, 255, 0.3); }
.nav-link-btn { color: var(--text-secondary); }
.nav-link-btn:hover { color: var(--neon-coral); }

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 14px 4px 4px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  margin-left: var(--space-2);
}
.user-avatar {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--gradient-btn);
  color: #fff;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.85rem;
}
.user-name {
  font-size: 0.85rem;
  color: var(--text-primary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .nav-inner { padding: 0 var(--space-4); }
  .logo-sub { display: none; }
  .user-name { display: none; }
}
</style>
