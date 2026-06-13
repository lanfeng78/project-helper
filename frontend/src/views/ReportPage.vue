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
      <div class="page-toolbar">
        <BackButton />
      </div>
      <div class="report-header glass-card">
        <div class="report-title-row">
          <div class="report-title-main">
            <div class="report-title-meta">
              <h1>{{ report.report_json?.project_name || report.repo_name }}</h1>
              <span
                v-if="report.analysis_mode"
                class="mode-badge"
                :class="`mode-badge-${report.analysis_mode}`"
              >{{ report.analysis_mode === 'simple' ? '简易' : '详细' }}</span>
            </div>
            <p class="report-one-line">{{ report.report_json?.one_line || '' }}</p>
          </div>
          <div class="report-actions">
            <button class="report-tool-btn" @click="onCopy" :title="copyTip">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <span>{{ copyTip }}</span>
            </button>
            <button class="report-tool-btn" @click="onExport" title="导出 Markdown">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>导出 .md</span>
            </button>
            <button class="btn btn-primary" @click="$router.push(`/qa/${report.project_id}`)">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              交互问答
            </button>
          </div>
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
import BackButton from '@/components/BackButton.vue'
import { copyText, downloadMarkdown, safeFilename } from '@/utils/exporter'

const route = useRoute()
const projectId = route.params.id
const report = ref(null)
const loading = ref(true)
const error = ref('')
const copyTip = ref('复制')
let copyTimer = null

onMounted(async () => {
  try { report.value = await getReport(projectId) }
  catch (e) { error.value = e.message }
  finally { loading.value = false }
})

async function onCopy() {
  if (!report.value) return
  const ok = await copyText(report.value.report_markdown || '')
  copyTip.value = ok ? '已复制' : '复制失败'
  if (copyTimer) clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copyTip.value = '复制' }, 2000)
}

function onExport() {
  if (!report.value) return
  const name = report.value.report_json?.project_name || report.value.repo_name || 'report'
  const mode = report.value.analysis_mode ? `_${report.value.analysis_mode}` : ''
  downloadMarkdown(`${safeFilename(name)}${mode}`, report.value.report_markdown || '')
}
</script>

<style scoped>
.report-page { max-width: 960px; margin: 0 auto; padding-top: var(--space-4); }

.page-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-3);
}

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
  flex-wrap: wrap;
}

.report-title-main { flex: 1; min-width: 0; }

.report-title-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.report-title-row h1 { font-size: 1.8rem; margin-bottom: var(--space-2); }

.report-one-line { color: var(--text-secondary); font-size: 1rem; }

.report-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.report-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.06), rgba(224, 64, 251, 0.06));
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 200ms ease;
  min-height: 36px;
}
.report-tool-btn:hover {
  color: var(--neon-cyan);
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.2), 0 6px 18px -10px rgba(0, 229, 255, 0.4);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.12), rgba(224, 64, 251, 0.08));
}
.report-tool-btn:focus-visible {
  outline: 2px solid var(--neon-cyan);
  outline-offset: 2px;
}

.mode-badge {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-medium);
  line-height: 1.6;
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

.report-body {
  padding: var(--space-8);
  min-height: 500px;
}

@media (max-width: 768px) {
  .report-title-row { flex-direction: column; }
  .report-body { padding: var(--space-5); }
}
</style>
