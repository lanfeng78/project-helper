<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero">
      <div class="section-tag">▸ Project Helper <span class="num">/ 01</span></div>
      <div class="hero-badges">
        <span class="badge badge-cyan">DeepSeek V4</span>
        <span class="badge badge-magenta">LangChain</span>
        <span class="badge badge-lime">FastAPI</span>
      </div>

      <h1 class="hero-title">
        <span class="title-line">读懂任何开源项目</span>
        <span class="title-gradient">就像查字典一样简单</span>
      </h1>

      <p class="hero-desc">
        粘贴 GitHub 链接，AI 自动克隆分析源码，生成<span class="highlight">连初学者都能看懂</span>的完整报告。
        支持交互问答——像有一位资深架构师坐在你旁边。
      </p>

      <!-- Input -->
      <div class="input-group">
        <div class="input-wrapper">
          <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          <input
            ref="inputRef"
            v-model="repoUrl"
            class="input-hero"
            placeholder="https://github.com/facebook/react"
            @keyup.enter="startAnalysis"
          />
        </div>
        <button
          class="btn btn-primary btn-hero"
          @click="startAnalysis"
          :disabled="loading"
        >
          <template v-if="!loading">
            <span>开始分析</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </template>
          <span v-else class="spinner"></span>
        </button>
      </div>

      <!-- Analysis Mode Toggle -->
      <div class="mode-toggle" role="radiogroup" aria-label="分析模式">
        <span class="mode-toggle-label">分析模式</span>
        <div class="mode-toggle-group">
          <button
            type="button"
            class="mode-pill"
            :class="{ active: mode === 'simple' }"
            :aria-checked="mode === 'simple'"
            role="radio"
            @click="mode = 'simple'"
          >
            <span class="mode-pill-title">简易</span>
            <span class="mode-pill-sub">flash · 快速概览</span>
          </button>
          <button
            type="button"
            class="mode-pill"
            :class="{ active: mode === 'detail' }"
            :aria-checked="mode === 'detail'"
            role="radio"
            @click="mode = 'detail'"
          >
            <span class="mode-pill-title">详细</span>
            <span class="mode-pill-sub">pro · 13 维分析</span>
          </button>
        </div>
      </div>

      <Transition name="fade">
        <p v-if="error" class="error-msg">{{ error }}</p>
      </Transition>
    </section>

    <!-- Bento Grid Features -->
    <section class="bento-grid-wrap">
      <div class="section-tag">▸ Capabilities <span class="num">/ 02</span></div>
      <div class="bento-grid">
      <div class="bento-card bento-report glass-card">
        <div class="bento-icon" style="background: var(--neon-cyan-10)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="1.8">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
        </div>
        <h3>智能分析报告</h3>
        <p>项目概述、技术栈、核心模块、数据流、设计模式，生成连初学者都能看懂的完整文档</p>
        <ul class="bento-tags">
          <li>13 维度分析</li>
          <li>中文报告</li>
          <li>Markdown 输出</li>
        </ul>
      </div>

      <div class="bento-card bento-qa glass-card">
        <div class="bento-icon" style="background: var(--neon-magenta-10)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--neon-magenta)" stroke-width="1.8">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <h3>交互式问答</h3>
        <p>对源码有任何疑问直接问，AI 会自主搜索代码来回答，像与作者面对面交流</p>
        <ul class="bento-tags">
          <li>流式输出</li>
          <li>上下文记忆</li>
          <li>代码引用</li>
        </ul>
      </div>

      <div class="bento-card bento-speed glass-card">
        <div class="bento-icon" style="background: var(--neon-cyan-10)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--neon-cyan)" stroke-width="1.8">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h3>实时进度</h3>
        <p>克隆→扫描→AI 分析全过程可见，进度条实时更新，已分析项目自动缓存无需重复</p>
      </div>

      <div class="bento-card bento-stats glass-card">
        <div class="stat-row">
          <div class="stat">
            <span class="stat-value">13</span>
            <span class="stat-label">分析维度</span>
          </div>
          <div class="stat">
            <span class="stat-value">15+</span>
            <span class="stat-label">支持语言</span>
          </div>
          <div class="stat">
            <span class="stat-value">O(1)</span>
            <span class="stat-label">缓存命中</span>
          </div>
        </div>
      </div>
      </div>
    </section>

    <!-- Recent Projects -->
    <section v-if="projects.length" class="recent-section">
      <div class="section-tag">▸ Recent <span class="num">/ 03</span></div>
      <div class="section-header">
        <h2>最近分析</h2>
        <span class="section-count">{{ projects.length }} 个项目</span>
      </div>
      <div class="project-grid">
        <div
          v-for="p in projects"
          :key="p.id"
          class="project-card glass-card"
          role="button"
          tabindex="0"
          @click="$router.push(`/report/${p.id}`)"
          @keydown.enter.prevent="$router.push(`/report/${p.id}`)"
          @keydown.space.prevent="$router.push(`/report/${p.id}`)"
        >
          <div class="project-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
            </svg>
          </div>
          <div class="project-meta">
            <div class="project-name-row">
              <span class="project-name">{{ p.repo_name }}</span>
              <span
                class="mode-badge"
                :class="`mode-badge-${p.analysis_mode || 'detail'}`"
              >{{ (p.analysis_mode || 'detail') === 'simple' ? '简易' : '详细' }}</span>
            </div>
            <div class="project-url">{{ p.repo_url }}</div>
          </div>
          <div class="project-trail" @click.stop>
            <template v-if="confirmingId === p.id">
              <button
                class="btn-confirm btn-confirm-yes"
                @click.stop="reallyRemove(p.id)"
                :disabled="deleting === p.id"
                :title="deleting === p.id ? '删除中…' : '确认删除'"
              >
                <span v-if="deleting !== p.id" aria-hidden="true">✓</span>
                <span v-else class="btn-delete-spinner" aria-hidden="true"></span>
              </button>
              <button
                class="btn-confirm btn-confirm-no"
                @click.stop="cancelRemove"
                title="取消"
              >
                <span aria-hidden="true">✕</span>
              </button>
            </template>
            <button
              v-else
              class="btn-delete"
              @click.stop="askRemove(p.id)"
              title="删除"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { analyzeRepo, listProjects, deleteProject } from '@/api'

const router = useRouter()
const repoUrl = ref('')
const loading = ref(false)
const error = ref('')
const projects = ref([])
const deleting = ref(null)
const mode = ref('detail')

// inline-confirm state for delete
const confirmingId = ref(null)
let confirmTimer = null

onMounted(async () => {
  try { projects.value = await listProjects() } catch {}
})

function isValidUrl(url) {
  return /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+/.test(url.trim())
}

function askRemove(id) {
  confirmingId.value = id
  if (confirmTimer) clearTimeout(confirmTimer)
  // auto-collapse the confirm chips after 3s of inactivity
  confirmTimer = setTimeout(() => {
    if (confirmingId.value === id) confirmingId.value = null
  }, 3000)
}

function cancelRemove() {
  confirmingId.value = null
  if (confirmTimer) { clearTimeout(confirmTimer); confirmTimer = null }
}

async function reallyRemove(id) {
  if (confirmTimer) { clearTimeout(confirmTimer); confirmTimer = null }
  deleting.value = id
  try {
    await deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
  } catch (e) {
    console.error(e)
  } finally {
    deleting.value = null
    confirmingId.value = null
  }
}

async function startAnalysis() {
  error.value = ''
  const url = repoUrl.value.trim()
  if (!url) { error.value = '请输入 GitHub 仓库地址'; return }
  if (!isValidUrl(url)) { error.value = '请输入有效的地址，如 https://github.com/user/repo'; return }

  loading.value = true
  try {
    const result = await analyzeRepo(url, mode.value)
    if (result.cached) router.push(`/report/${result.project_id}`)
    else router.push(`/analyze/${result.project_id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-page { padding-top: var(--space-10); }

/* ═══════════════ HERO ═══════════════ */
.hero {
  text-align: center;
  padding: var(--space-10) var(--space-4) var(--space-12);
  position: relative;
}

.hero-badges {
  display: flex;
  gap: var(--space-2);
  justify-content: center;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
}

.hero-title {
  margin-bottom: var(--space-5);
}

.title-line {
  display: block;
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  animation: fadeUp 0.6s var(--ease-out-expo);
}

.title-gradient {
  display: block;
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: fadeUp 0.6s var(--ease-out-expo) 0.15s both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-desc {
  font-size: 1.1rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto var(--space-8);
  line-height: 1.75;
  animation: fadeUp 0.6s var(--ease-out-expo) 0.3s both;
}

.highlight {
  color: var(--neon-lime);
  font-weight: 600;
}

/* Input group */
.input-group {
  display: flex;
  gap: var(--space-3);
  max-width: 660px;
  margin: 0 auto;
  animation: fadeUp 0.6s var(--ease-out-expo) 0.45s both;
}

.input-wrapper { flex: 1; position: relative; }

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--text-muted);
}

.input-hero {
  width: 100%;
  padding: 16px 18px 16px 50px;
  background: var(--bg-field);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 0.9rem;
  outline: none;
  transition: all var(--duration-normal) var(--ease-out-expo);
}

.input-hero::placeholder { color: var(--text-muted); font-family: var(--font-sans); }
.input-hero:hover { border-color: var(--border-glow); }
.input-hero:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 4px var(--neon-cyan-15), 0 0 24px rgba(0, 229, 255, 0.06);
}

.btn-hero {
  padding: 16px 32px;
  font-size: 1rem;
  white-space: nowrap;
  gap: 10px;
}

.error-msg {
  color: var(--neon-coral);
  margin-top: var(--space-4);
  font-size: 0.9rem;
  padding: 10px 20px;
  background: rgba(255, 82, 82, 0.08);
  border: 1px solid rgba(255, 82, 82, 0.2);
  border-radius: var(--radius-full);
  display: inline-block;
}

.spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,0.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ═══════════════ BENTO GRID ═══════════════ */
.bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: var(--space-5);
  max-width: 960px;
  margin: 0 auto var(--space-12);
}

.bento-report { grid-column: 1 / 3; grid-row: 1; }
.bento-qa { grid-column: 3; grid-row: 1; }
.bento-speed { grid-column: 1; grid-row: 2; }
.bento-stats { grid-column: 2 / 4; grid-row: 2; }

.bento-card {
  padding: var(--space-6);
}

.bento-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
}

.bento-card h3 {
  font-size: 1.1rem;
  margin-bottom: var(--space-2);
}

.bento-card p {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.65;
  margin-bottom: var(--space-4);
}

.bento-tags {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  list-style: none;
}

.bento-tags li {
  padding: 3px 12px;
  font-size: 0.72rem;
  color: var(--text-muted);
  background: var(--bg-field);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
}

/* Stats */
.stat-row {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 100%;
  padding: var(--space-3) 0;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 2.2rem;
  font-weight: 800;
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-family: var(--font-mono);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: var(--space-1);
}

/* ═══════════════ RECENT PROJECTS ═══════════════ */
.recent-section { padding-bottom: var(--space-16); }

.section-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.section-count {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.project-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.project-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  cursor: pointer;
}
.project-card:focus-visible {
  outline: 2px solid var(--neon-cyan);
  outline-offset: 2px;
}

.project-meta {
  flex: 1;
  min-width: 0;
}

.project-icon {
  width: 40px; height: 40px;
  border-radius: var(--radius-sm);
  background: var(--bg-field);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  flex-shrink: 0;
}

.project-card:hover .project-icon { color: var(--neon-cyan); }

.project-name {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 2px;
}

.project-url {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.project-arrow {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 1.1rem;
  transition: all var(--duration-fast);
}

.btn-delete {
  width: 36px; height: 36px;
  border: none; background: transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--duration-fast);
  flex-shrink: 0;
  opacity: 0;
}
.project-card:hover .btn-delete { opacity: 1; }
.btn-delete:hover {
  color: var(--neon-coral);
  background: rgba(255, 82, 82, 0.1);
}
.btn-delete-spinner {
  width: 14px; height: 14px;
  border: 2px solid var(--border-medium);
  border-top-color: var(--neon-coral);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}

/* Trail wrapper holds either the trash icon or the inline-confirm chips */
.project-trail {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* Inline-confirm chips (visible whenever they render — no hover gate) */
.btn-confirm {
  width: 32px; height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-medium);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95rem;
  font-weight: 700;
  font-family: var(--font-mono);
  transition: all var(--duration-fast);
}
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-confirm-yes {
  border-color: rgba(255, 82, 82, 0.45);
  color: var(--neon-coral);
}
.btn-confirm-yes:hover:not(:disabled) {
  background: rgba(255, 82, 82, 0.18);
  border-color: var(--neon-coral);
  box-shadow: 0 0 12px rgba(255, 82, 82, 0.25);
}
.btn-confirm-no {
  color: var(--text-secondary);
}
.btn-confirm-no:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

/* Project name row + mode badge */
.project-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
  flex-wrap: wrap;
}
.mode-badge {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-medium);
  line-height: 1.4;
}
.mode-badge-simple {
  color: var(--neon-lime);
  border-color: rgba(118, 255, 3, 0.35);
  background: rgba(118, 255, 3, 0.08);
}
.mode-badge-detail {
  color: var(--neon-magenta);
  border-color: rgba(224, 64, 251, 0.35);
  background: var(--neon-magenta-10);
}

/* ═══════════════ MODE TOGGLE (segmented control) ═══════════════ */
.mode-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-4) auto 0;
  max-width: 600px;
  flex-wrap: wrap;
  justify-content: center;
}
.mode-toggle-label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.mode-toggle-group {
  display: inline-flex;
  padding: 4px;
  background: rgba(7, 6, 26, 0.55);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  gap: 4px;
}
.mode-pill {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 18px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast);
  min-width: 132px;
}
.mode-pill-title {
  font-weight: 600;
  font-size: 0.92rem;
  letter-spacing: 0.02em;
}
.mode-pill-sub {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}
.mode-pill:hover { color: var(--text-primary); }
.mode-pill.active {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.18), rgba(224, 64, 251, 0.18));
  border-color: var(--border-glow);
  color: var(--text-primary);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.2), 0 0 16px rgba(0, 229, 255, 0.15);
}
.mode-pill.active .mode-pill-sub { color: var(--neon-cyan); }
@media (max-width: 768px) {
  .mode-toggle { gap: var(--space-2); }
  .mode-pill { min-width: 110px; padding: 6px 12px; }
}

.project-card:hover .project-arrow { color: var(--neon-cyan); transform: translateX(4px); }

/* Fade transition */
.fade-enter-active { transition: opacity 0.3s ease, transform 0.3s var(--ease-out-expo); }
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-from { transform: translateY(-8px); }

/* ═══════════════ RESPONSIVE ═══════════════ */
@media (max-width: 768px) {
  .hero { padding: var(--space-6) var(--space-4) var(--space-8); }
  .input-group { flex-direction: column; }
  .btn-hero { justify-content: center; }
  .bento-grid { grid-template-columns: 1fr; }
  .bento-report, .bento-qa, .bento-speed, .bento-stats { grid-column: 1; }
}
</style>
