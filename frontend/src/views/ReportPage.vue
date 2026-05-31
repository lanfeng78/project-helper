<template>
  <div class="report-page">
    <div v-if="loading" class="loading-state">
      <div class="loading-ring"></div>
      <p>加载报告中...</p>
    </div>

    <div v-else-if="error" class="error-state glass-card">
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="$router.push('/')">← 返回首页</button>
    </div>

    <template v-else-if="report">
      <div class="report-header glass-card">
        <div class="report-title-row">
          <div>
            <h1>{{ report.report_json?.project_name || report.repo_name }}</h1>
            <p class="report-one-line">{{ report.report_json?.one_line || '' }}</p>
          </div>
          <button class="btn btn-primary" @click="$router.push(`/qa/${report.project_id}`)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            交互问答
          </button>
        </div>
      </div>

      <div class="report-body glass-card">
        <MarkdownRenderer :content="report.report_markdown || ''" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getReport } from '@/api'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const route = useRoute()
const projectId = route.params.id
const report = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try { report.value = await getReport(projectId) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
})
</script>

<style scoped>
.report-page { max-width: 960px; margin: 0 auto; padding-top: var(--space-4); }

.loading-state, .error-state {
  text-align: center;
  padding: var(--space-16) var(--space-4);
  color: var(--text-secondary);
}

.loading-ring {
  width: 44px; height: 44px;
  border: 3px solid var(--border-medium);
  border-top-color: var(--neon-cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin { to { transform: rotate(360deg); } }

.report-header {
  padding: var(--space-6) var(--space-8);
  margin-bottom: var(--space-5);
}

.report-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-5);
}

.report-title-row h1 { font-size: 1.8rem; margin-bottom: var(--space-2); }

.report-one-line { color: var(--text-secondary); font-size: 1rem; }

.report-body {
  padding: var(--space-8);
  min-height: 500px;
}

@media (max-width: 768px) {
  .report-title-row { flex-direction: column; }
  .report-body { padding: var(--space-5); }
}
</style>
