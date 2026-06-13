<template>
  <div class="qa-page">
    <div class="qa-layout">
      <!-- Chat Area -->
      <div class="qa-chat glass-card">
        <div class="qa-header">
          <BackButton />
          <h2>💬 源码问答</h2>
          <span class="qa-project-name"># {{ projectId.slice(0, 8) }}</span>
          <div class="qa-tools">
            <button
              class="qa-tool-btn"
              @click="onCopyAll"
              :disabled="streaming || !messages.length"
              :title="copyTip"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              <span>{{ copyTip }}</span>
            </button>
            <button
              class="qa-tool-btn"
              @click="onExportAll"
              :disabled="streaming || !messages.length"
              title="导出对话 .md"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>.md</span>
            </button>
            <button
              class="qa-tool-btn qa-tool-danger"
              @click="onClear"
              :disabled="streaming || !messages.length"
              title="清空对话"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div class="qa-messages" ref="msgContainer">
          <div v-if="messages.length === 0 && !streaming" class="qa-empty">
            <div class="empty-icon">🤔</div>
            <p>对源码有任何疑问？直接问我吧！</p>
            <div class="suggestions">
              <button
                v-for="(q, i) in suggestions"
                :key="i"
                class="suggestion-chip"
                @click="askQuestion(q)"
              >{{ q }}</button>
            </div>
          </div>

          <div v-for="(msg, i) in messages" :key="i" class="qa-message" :class="msg.role">
            <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="msg-content">
              <div class="msg-text" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>

          <!-- Streaming / Thinking -->
          <div v-if="streaming" class="qa-message assistant">
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
              <!-- Thinking state: no tokens yet -->
              <div v-if="thinking" class="thinking-indicator">
                <span class="thinking-label">AI 正在思考</span>
                <span class="thinking-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </span>
              </div>
              <!-- Token streaming: content arriving -->
              <template v-else>
                <div class="msg-text" v-html="renderMarkdown(streamContent)"></div>
                <span class="streaming-cursor"></span>
              </template>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="qa-input-area">
          <input
            v-model="question"
            class="qa-input"
            placeholder="输入你的问题..."
            @keyup.enter="askQuestion()"
            :disabled="streaming"
          />
          <button
            class="btn btn-primary qa-send"
            @click="askQuestion()"
            :disabled="!question.trim() || streaming"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { streamQA, getReport } from '@/api'
import BackButton from '@/components/BackButton.vue'
import { copyText, downloadMarkdown } from '@/utils/exporter'

const route = useRoute()
const projectId = route.params.id
const question = ref('')
const messages = ref([])
const streaming = ref(false)
const thinking = ref(false)
const streamContent = ref('')
const msgContainer = ref(null)
const copyTip = ref('复制')
let copyTimer = null

const suggestions = [
  "这个项目的入口文件是什么？",
  "核心模块有哪些？它们之间怎么协作？",
  "数据是怎么在系统里流转的？",
  "用了哪些设计模式？",
  "如果我是新手，应该从哪里开始看？"
]

onMounted(async () => {
  try { await getReport(projectId) } catch {}
})

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

async function askQuestion(q) {
  const queryText = (typeof q === 'string' ? q : question.value).trim()
  if (!queryText || streaming.value) return

  if (typeof q === 'string') question.value = q
  else question.value = ''

  messages.value.push({ role: 'user', content: queryText })
  await scrollToBottom()

  streaming.value = true
  thinking.value = true
  streamContent.value = ''

  const conversation = messages.value.slice(0, -1).map(m => ({
    role: m.role,
    content: m.content
  }))

  try {
    await streamQA(
      projectId,
      queryText,
      conversation,
      (token) => {
        thinking.value = false
        streamContent.value += token
      },
      () => {
        if (streamContent.value) {
          messages.value.push({ role: 'assistant', content: streamContent.value })
        }
        streamContent.value = ''
        thinking.value = false
        streaming.value = false
        scrollToBottom()
      },
      (err) => {
        messages.value.push({ role: 'assistant', content: `❌ 出错了：${err}` })
        thinking.value = false
        streaming.value = false
      }
    )
  } catch {
    thinking.value = false
    streaming.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

function formatConversation(msgs) {
  const head = `# 源码问答 · ${projectId}\n\n_由 Project Helper 导出_\n\n`
  const body = msgs.map(m => {
    const tag = m.role === 'user' ? '## 🧑 你' : '## 🤖 AI'
    return `${tag}\n\n${m.content}\n`
  }).join('\n---\n\n')
  return head + body
}

async function onCopyAll() {
  if (!messages.value.length) return
  const ok = await copyText(formatConversation(messages.value))
  copyTip.value = ok ? '已复制' : '复制失败'
  if (copyTimer) clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copyTip.value = '复制' }, 2000)
}

function onExportAll() {
  if (!messages.value.length) return
  downloadMarkdown(`qa-${projectId.slice(0, 8)}`, formatConversation(messages.value))
}

function onClear() {
  if (!messages.value.length) return
  if (!window.confirm('清空当前对话?此操作不可撤销。')) return
  messages.value = []
  streamContent.value = ''
}
</script>

<style scoped>
.qa-page { max-width: 900px; margin: 0 auto; height: calc(100vh - 100px); }

.qa-layout { height: 100%; }

.qa-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.qa-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-medium);
  flex-wrap: wrap;
}

.qa-header h2 { font-size: 1.1rem; }

.qa-project-name {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-muted);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-tools {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.qa-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.05), rgba(224, 64, 251, 0.05));
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 180ms ease;
  min-height: 30px;
}
.qa-tool-btn:hover:not(:disabled) {
  color: var(--neon-cyan);
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.18);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.10), rgba(224, 64, 251, 0.06));
}
.qa-tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.qa-tool-btn:focus-visible {
  outline: 2px solid var(--neon-cyan);
  outline-offset: 2px;
}
.qa-tool-danger:hover:not(:disabled) {
  color: var(--neon-coral);
  border-color: var(--neon-coral);
  box-shadow: 0 0 0 1px rgba(255, 82, 82, 0.25);
  background: rgba(255, 82, 82, 0.08);
}

/* Messages */
.qa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.qa-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.empty-icon { font-size: 3rem; margin-bottom: 12px; }

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 20px;
}

.suggestion-chip {
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.suggestion-chip:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: var(--accent-cyan-dim);
}

/* Message bubbles */
.qa-message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.qa-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-input);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.msg-content {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  line-height: 1.7;
}

.qa-message.user .msg-content {
  background: var(--accent-cyan-dim);
  border-color: rgba(0, 212, 255, 0.2);
}

.msg-text { font-size: 0.92rem; }

.msg-text :deep(p) { margin: 4px 0; }
.msg-text :deep(pre) { margin: 8px 0; font-size: 0.8rem; }
.msg-text :deep(code) { font-size: 0.85em; }

/* ═══════════════ THINKING INDICATOR ═══════════════ */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.thinking-label {
  font-size: 0.88rem;
  color: var(--text-secondary);
  font-style: italic;
}

.thinking-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.thinking-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-cyan);
  animation: dotBounce 1.4s ease-in-out infinite;
}

.thinking-dots .dot:nth-child(1) { animation-delay: 0s; }
.thinking-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotBounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.3;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* Streaming cursor */
.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--accent-cyan);
  animation: blink 0.8s infinite;
  vertical-align: middle;
  margin-left: 2px;
}

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* Input */
.qa-input-area {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.qa-input {
  flex: 1;
  padding: 12px 16px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.92rem;
  outline: none;
  transition: border-color var(--transition-fast);
}

.qa-input:focus { border-color: var(--accent-cyan); }
.qa-input::placeholder { color: var(--text-muted); }

.qa-send { padding: 10px 24px; }
</style>
