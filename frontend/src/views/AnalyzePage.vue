<template>
  <div class="analyze-page">
    <div class="page-toolbar">
      <BackButton />
    </div>
    <div class="analyze-card glass-card">
      <div class="analyze-header">
        <div class="status-icon" :class="{ done: isDone, error: isError }">
          <span v-if="isError">✗</span>
          <span v-else-if="isDone">✓</span>
          <span v-else class="pulse-dot"></span>
        </div>
        <div>
          <h2>{{ isError ? '分析失败' : isDone ? '分析完成' : '正在分析项目...' }}</h2>
          <p class="repo-name">{{ repoUrl }}</p>
        </div>
      </div>

      <ProgressBar :percent="progress" :message="progressMsg" />

      <div v-if="isError" class="error-block">
        <p class="error-text">{{ errorMsg }}</p>
        <div class="error-actions">
          <button class="btn btn-primary" @click="retry">重试分析</button>
          <button class="btn btn-secondary" @click="$router.push('/')">返回首页</button>
        </div>
      </div>

      <div v-if="isDone" class="done-actions">
        <button class="btn btn-primary" @click="goToReport">查看报告</button>
        <button class="btn btn-secondary" @click="goToQA">交互问答</button>
      </div>

      <!-- Analysis steps visualization -->
      <div v-if="!isDone && !isError" class="steps">
        <div class="step" :class="{ active: progress >= 5, done: progress >= 55 }">
          <span class="step-num">1</span>
          <span class="step-label">克隆仓库</span>
        </div>
        <div class="step-connector" :class="{ active: progress >= 55 }"></div>
        <div class="step" :class="{ active: progress >= 55, done: progress >= 75 }">
          <span class="step-num">2</span>
          <span class="step-label">扫描代码</span>
        </div>
        <div class="step-connector" :class="{ active: progress >= 75 }"></div>
        <div class="step" :class="{ active: progress >= 75, done: progress >= 100 }">
          <span class="step-num">3</span>
          <span class="step-label">AI 分析</span>
        </div>
        <div class="step-connector" :class="{ active: progress >= 100 }"></div>
        <div class="step" :class="{ active: progress >= 100 }">
          <span class="step-num">4</span>
          <span class="step-label">生成报告</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { subscribeProgress, analyzeRepo } from '@/api'
import BackButton from '@/components/BackButton.vue'
import ProgressBar from '@/components/ProgressBar.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const repoUrl = ref('...')

const progress = ref(0)
const progressMsg = ref('准备中...')
const isDone = ref(false)
const isError = ref(false)
const errorMsg = ref('')

let subscription = null

onMounted(() => {
  subscription = subscribeProgress(
    projectId,
    (data) => {
      if (data.progress !== undefined) progress.value = data.progress
      if (data.msg) progressMsg.value = data.msg
    },
    () => { isDone.value = true },
    (data) => {
      isError.value = true
      errorMsg.value = data.msg || '未知错误'
    }
  )
})

onUnmounted(() => {
  if (subscription) subscription.close()
})

function goToReport() { router.push(`/report/${projectId}`) }
function goToQA() { router.push(`/qa/${projectId}`) }

async function retry() {
  isError.value = false
  progress.value = 0
  progressMsg.value = '重新分析中...'
  if (subscription) subscription.close()
  try {
    const result = await analyzeRepo(repoUrl.value || '')
    subscription = subscribeProgress(
      result.project_id,
      (data) => {
        if (data.progress !== undefined) progress.value = data.progress
        if (data.msg) progressMsg.value = data.msg
      },
      () => { isDone.value = true },
      (data) => {
        isError.value = true
        errorMsg.value = data.msg || '未知错误'
      }
    )
  } catch (e) {
    isError.value = true
    errorMsg.value = e.message
  }
}
</script>

<style scoped>
.analyze-page {
  max-width: 640px;
  margin: 60px auto;
}

.page-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-3);
}

.analyze-card {
  padding: 32px;
}

.analyze-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  background: var(--accent-cyan-dim);
  color: var(--accent-cyan);
  flex-shrink: 0;
}

.status-icon.done { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }
.status-icon.error { background: rgba(239, 68, 68, 0.15); color: var(--accent-red); }

.pulse-dot {
  width: 12px;
  height: 12px;
  background: var(--accent-cyan);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

.repo-name {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 4px;
}

.error-block {
  margin-top: 20px;
  padding: 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-sm);
}

.error-text {
  color: var(--accent-red);
  font-size: 0.9rem;
  margin-bottom: 12px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 10px;
}

.done-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

/* Steps */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 32px;
  gap: 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  opacity: 0.3;
  transition: all var(--transition-normal);
}

.step.active { opacity: 0.7; }
.step.done { opacity: 1; }

.step-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
  background: var(--bg-input);
  border: 2px solid var(--border-color);
  transition: all var(--transition-normal);
}

.step.active .step-num { border-color: var(--accent-cyan); color: var(--accent-cyan); }
.step.done .step-num { background: var(--accent-cyan); border-color: var(--accent-cyan); color: #fff; }

.step-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.step-connector {
  width: 40px;
  height: 2px;
  background: var(--border-color);
  margin: 0 4px 20px;
  transition: background var(--transition-normal);
}

.step-connector.active { background: var(--accent-cyan); }
</style>
