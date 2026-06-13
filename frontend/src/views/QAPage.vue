<template>
  <div class="qa-page">
    <div class="qa-layout">
      <!-- ═══════════════ Sidebar (会话历史) ═══════════════ -->
      <aside class="qa-sidebar glass-card">
        <div class="qa-sidebar-head">
          <span class="qa-sidebar-title">对话历史</span>
          <button
            class="qa-new-btn"
            @click="onNewSession"
            :disabled="streaming"
            title="新建对话"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span>新对话</span>
          </button>
        </div>

        <div class="qa-sessions">
          <div v-if="sessionsLoading" class="qa-sessions-empty">加载中...</div>
          <div v-else-if="!sessions.length" class="qa-sessions-empty">
            <span class="empty-hint">暂无对话</span>
            <span class="empty-sub">提问以开始首次对话</span>
          </div>
          <div
            v-for="s in sessions"
            :key="s.id"
            class="qa-session-item"
            :class="{ active: s.id === currentSessionId }"
            @click="switchSession(s.id)"
          >
            <div class="qa-session-marker"></div>
            <div class="qa-session-body">
              <input
                v-if="renamingId === s.id"
                v-model="renameDraft"
                class="qa-session-rename"
                @click.stop
                @keyup.enter="commitRename(s.id)"
                @keyup.esc="cancelRename"
                @blur="commitRename(s.id)"
                ref="renameInput"
              />
              <div v-else class="qa-session-title" :title="s.title">{{ s.title }}</div>
              <div class="qa-session-time">{{ formatTime(s.updated_at) }}</div>
            </div>
            <div class="qa-session-actions" @click.stop>
              <button
                class="qa-session-mini"
                @click.stop="startRename(s)"
                :disabled="streaming"
                title="重命名"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                  <path d="M12 20h9"/>
                  <path d="M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4z"/>
                </svg>
              </button>
              <button
                class="qa-session-mini qa-session-mini-danger"
                @click.stop="confirmDeleteSession(s)"
                :disabled="streaming"
                title="删除会话"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </aside>

      <!-- ═══════════════ Chat Area ═══════════════ -->
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
          </div>
        </div>

        <!-- Messages -->
        <div
          class="qa-messages"
          ref="msgContainer"
          @scroll="onScroll"
          @wheel="onUserInteract"
          @touchmove="onUserInteract"
        >
          <div v-if="messages.length === 0 && !streaming && !historyLoading" class="qa-empty">
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

          <div v-if="historyLoading" class="qa-history-loading">
            <span class="loading-bar"></span>
            <span>加载历史对话...</span>
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
              <div v-if="thinking" class="thinking-indicator">
                <span class="thinking-label">AI 正在思考</span>
                <span class="thinking-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </span>
              </div>
              <template v-else>
                <div class="msg-text" v-html="renderMarkdown(streamContent)"></div>
                <span class="streaming-cursor"></span>
              </template>
            </div>
          </div>
        </div>

        <!-- 回到底部 浮标(用户上滚后显示) -->
        <Transition name="float">
          <button
            v-if="!autoFollow && (messages.length || streaming)"
            class="qa-jump-bottom"
            @click="resumeAutoFollow"
            title="回到底部"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <polyline points="19 12 12 19 5 12"/>
            </svg>
          </button>
        </Transition>

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
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import {
  streamQA,
  getReport,
  listQASessions,
  createQASession,
  getQAMessages,
  renameQASession,
  deleteQASession,
} from '@/api'
import BackButton from '@/components/BackButton.vue'
import { copyText, downloadMarkdown } from '@/utils/exporter'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

// ── 聊天状态 ──
const question = ref('')
const messages = ref([])
const streaming = ref(false)
const thinking = ref(false)
const streamContent = ref('')
const msgContainer = ref(null)
const copyTip = ref('复制')
let copyTimer = null

// ── 会话状态 ──
const sessions = ref([])
const sessionsLoading = ref(true)
const currentSessionId = ref(route.query.s || null)
const historyLoading = ref(false)
const renamingId = ref(null)
const renameDraft = ref('')
const renameInput = ref(null)

// ── 滚动跟手 ──
const autoFollow = ref(true)
const NEAR_BOTTOM_PX = 80

const suggestions = [
  "这个项目的入口文件是什么？",
  "核心模块有哪些？它们之间怎么协作？",
  "数据是怎么在系统里流转的？",
  "用了哪些设计模式？",
  "如果我是新手，应该从哪里开始看？"
]

onMounted(async () => {
  // 拉一次报告(为了校验项目存在 + 让侧边逻辑确定项目就绪)
  try { await getReport(projectId) } catch {}
  await loadSessions()

  if (currentSessionId.value) {
    // URL 上指定了 session,优先加载它
    if (sessions.value.some(s => s.id === currentSessionId.value)) {
      await loadHistory(currentSessionId.value)
    } else {
      // URL 上的 sid 已经不存在了(可能被删了),退回最近一条
      currentSessionId.value = sessions.value[0]?.id || null
      syncQuery()
      if (currentSessionId.value) await loadHistory(currentSessionId.value)
    }
  } else if (sessions.value.length) {
    // 默认载入最近一条会话(豆包行为)
    currentSessionId.value = sessions.value[0].id
    syncQuery()
    await loadHistory(currentSessionId.value)
  }
  // 没有任何会话 → 保持空白,首次提问时后端会自动创建
})

watch(() => route.query.s, (sid) => {
  if (sid && sid !== currentSessionId.value) {
    currentSessionId.value = sid
    loadHistory(sid)
  }
})

// ─────────────────── 会话 / 历史 ───────────────────

async function loadSessions() {
  sessionsLoading.value = true
  try {
    sessions.value = await listQASessions(projectId)
  } catch (e) {
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

async function loadHistory(sid) {
  if (!sid) { messages.value = []; return }
  historyLoading.value = true
  try {
    const data = await getQAMessages(sid)
    messages.value = data.messages || []
    // 切换会话默认回到底部
    autoFollow.value = true
    await nextTick()
    forceScrollToBottom()
  } catch (e) {
    messages.value = []
  } finally {
    historyLoading.value = false
  }
}

async function switchSession(sid) {
  if (sid === currentSessionId.value || streaming.value) return
  currentSessionId.value = sid
  syncQuery()
  await loadHistory(sid)
}

async function onNewSession() {
  if (streaming.value) return
  try {
    const sess = await createQASession(projectId)
    sessions.value.unshift(sess)
    currentSessionId.value = sess.id
    syncQuery()
    messages.value = []
    autoFollow.value = true
  } catch (e) {
    /* 静默失败,用户可以再试一次 */
  }
}

function startRename(s) {
  renamingId.value = s.id
  renameDraft.value = s.title || ''
  nextTick(() => {
    const inp = Array.isArray(renameInput.value) ? renameInput.value[0] : renameInput.value
    if (inp) { inp.focus(); inp.select() }
  })
}

function cancelRename() {
  renamingId.value = null
  renameDraft.value = ''
}

async function commitRename(sid) {
  if (renamingId.value !== sid) return
  const title = (renameDraft.value || '').trim()
  const old = sessions.value.find(s => s.id === sid)
  renamingId.value = null
  if (!title || !old || title === old.title) { renameDraft.value = ''; return }
  try {
    const r = await renameQASession(sid, title)
    if (old) old.title = r.title
  } catch {}
  renameDraft.value = ''
}

async function confirmDeleteSession(s) {
  if (streaming.value) return
  if (!window.confirm(`删除对话「${s.title}」?`)) return
  try {
    await deleteQASession(s.id)
    const idx = sessions.value.findIndex(x => x.id === s.id)
    if (idx >= 0) sessions.value.splice(idx, 1)
    if (currentSessionId.value === s.id) {
      currentSessionId.value = sessions.value[0]?.id || null
      syncQuery()
      if (currentSessionId.value) await loadHistory(currentSessionId.value)
      else messages.value = []
    }
  } catch {}
}

function syncQuery() {
  const q = { ...route.query }
  if (currentSessionId.value) q.s = currentSessionId.value
  else delete q.s
  router.replace({ query: q })
}

// ─────────────────── 提问 / 流式 ───────────────────

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
  // 用户主动发起新提问 → 强制回到底部并恢复跟手
  autoFollow.value = true
  await nextTick()
  forceScrollToBottom()

  streaming.value = true
  thinking.value = true
  streamContent.value = ''

  // 仅传递历史消息中除最后一条(刚 push 的 user)之外的内容,后端也会以
  // 库内历史为准重新组装,这里只是兼容 stateless 路径。
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
        if (autoFollow.value) {
          // 用 rAF 把滚动合并到下一帧,避免每个 token 触发一次同步重排
          requestAnimationFrame(forceScrollToBottom)
        }
      },
      async (newSessionId) => {
        if (streamContent.value) {
          messages.value.push({ role: 'assistant', content: streamContent.value })
        }
        streamContent.value = ''
        thinking.value = false
        streaming.value = false
        // 如果是后端新建的会话,把它写进 URL 并刷新侧边栏
        if (newSessionId && newSessionId !== currentSessionId.value) {
          currentSessionId.value = newSessionId
          syncQuery()
        }
        // 不阻塞 UI,异步刷新侧边栏拿到最新 title / updated_at 排序
        loadSessions()
        if (autoFollow.value) {
          await nextTick()
          forceScrollToBottom()
        }
      },
      (err) => {
        messages.value.push({ role: 'assistant', content: `❌ 出错了：${err}` })
        thinking.value = false
        streaming.value = false
      },
      currentSessionId.value
    )
  } catch {
    thinking.value = false
    streaming.value = false
  }
}

// ─────────────────── 滚动 ───────────────────

function forceScrollToBottom() {
  const el = msgContainer.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

function onScroll() {
  const el = msgContainer.value
  if (!el) return
  const distance = el.scrollHeight - el.scrollTop - el.clientHeight
  // 用户回到底部 80px 内 → 自动恢复跟手;不在则关闭跟手
  // (forceScrollToBottom 会触发本回调,但因 distance≈0 也只是把状态稳定在 true)
  autoFollow.value = distance <= NEAR_BOTTOM_PX
}

// 用户发出明确"想看上面"的意图时立刻关跟手,不等 onScroll 阈值。
function onUserInteract(e) {
  if (e && e.type === 'wheel' && e.deltaY < 0) {
    autoFollow.value = false
  }
  // touchmove 让 onScroll 的阈值算法接管,无需在这里强行关掉
}

function resumeAutoFollow() {
  autoFollow.value = true
  forceScrollToBottom()
}

// ─────────────────── 复制 / 导出 ───────────────────

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

// ─────────────────── 杂项 ───────────────────

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} 天前`
  return d.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.qa-page { max-width: 1200px; margin: 0 auto; height: calc(100vh - 100px); }

.qa-layout {
  height: 100%;
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 16px;
}

/* ═══════════════ SIDEBAR ═══════════════ */
.qa-sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px 12px 12px;
  gap: 12px;
}

.qa-sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.qa-sidebar-title {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.qa-new-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.10), rgba(224, 64, 251, 0.06));
  border: 1px solid rgba(0, 229, 255, 0.30);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 180ms ease;
}
.qa-new-btn:hover:not(:disabled) {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.25);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.18), rgba(224, 64, 251, 0.10));
}
.qa-new-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.qa-sessions {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
}

.qa-sessions-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 32px 8px;
  color: var(--text-muted);
  font-size: 0.78rem;
}
.empty-hint { color: var(--text-secondary); }
.empty-sub { font-size: 0.7rem; opacity: 0.7; }

.qa-session-item {
  position: relative;
  display: flex;
  align-items: stretch;
  gap: 8px;
  padding: 9px 10px 9px 14px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 180ms ease;
  min-width: 0;
}

.qa-session-item:hover {
  background: rgba(0, 229, 255, 0.04);
  border-color: var(--border-medium);
}

.qa-session-marker {
  position: absolute;
  left: 4px;
  top: 12px;
  bottom: 12px;
  width: 2px;
  border-radius: 2px;
  background: transparent;
  transition: background 180ms ease;
}

.qa-session-item.active {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.12), rgba(224, 64, 251, 0.06));
  border-color: rgba(0, 229, 255, 0.30);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.10);
}
.qa-session-item.active .qa-session-marker {
  background: linear-gradient(180deg, var(--neon-cyan), var(--neon-magenta));
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.6);
}

.qa-session-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.qa-session-title {
  font-size: 0.84rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.35;
}

.qa-session-time {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.qa-session-rename {
  width: 100%;
  font-size: 0.84rem;
  background: var(--bg-input);
  color: var(--text-primary);
  border: 1px solid var(--neon-cyan);
  border-radius: 4px;
  padding: 2px 6px;
  outline: none;
}

.qa-session-actions {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  opacity: 0;
  transition: opacity 150ms ease;
  flex-shrink: 0;
}
.qa-session-item:hover .qa-session-actions { opacity: 1; }

.qa-session-mini {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid var(--border-medium);
  border-radius: 4px;
  cursor: pointer;
  transition: all 150ms ease;
}
.qa-session-mini:hover:not(:disabled) {
  color: var(--neon-cyan);
  border-color: var(--neon-cyan);
}
.qa-session-mini-danger:hover:not(:disabled) {
  color: var(--neon-coral, #ff5252);
  border-color: var(--neon-coral, #ff5252);
}
.qa-session-mini:disabled { opacity: 0.3; cursor: not-allowed; }

/* ═══════════════ CHAT ═══════════════ */
.qa-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  min-width: 0;
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

/* Messages */
.qa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: auto; /* 自动滚动用 scrollTop=scrollHeight,smooth 会和 rAF 打架 */
}

.qa-history-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-muted);
  border: 1px dashed var(--border-medium);
  border-radius: var(--radius-md);
  align-self: flex-start;
}
.loading-bar {
  width: 28px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
  background-size: 50% 100%;
  background-repeat: no-repeat;
  animation: bar-slide 1.2s linear infinite;
}
@keyframes bar-slide {
  0%   { background-position: -50% 0; }
  100% { background-position: 150% 0; }
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

/* ═══════════════ THINKING ═══════════════ */
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
  0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
  30% { transform: translateY(-8px); opacity: 1; }
}

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

/* ═══════════════ JUMP-BOTTOM FAB ═══════════════ */
.qa-jump-bottom {
  position: absolute;
  right: 22px;
  bottom: 88px;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid rgba(0, 229, 255, 0.45);
  color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(15, 13, 44, 0.92), rgba(10, 8, 34, 0.92));
  cursor: pointer;
  box-shadow: 0 6px 20px -8px rgba(0, 229, 255, 0.5),
              0 0 0 1px rgba(0, 229, 255, 0.15);
  backdrop-filter: blur(8px);
  transition: all 180ms ease;
  z-index: 5;
}
.qa-jump-bottom:hover {
  transform: translateY(-2px);
  border-color: var(--neon-cyan);
  box-shadow: 0 10px 24px -8px rgba(0, 229, 255, 0.7),
              0 0 0 1px rgba(0, 229, 255, 0.30);
}
.float-enter-active, .float-leave-active { transition: all 200ms ease; }
.float-enter-from, .float-leave-to { opacity: 0; transform: translateY(8px); }

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

/* ═══════════════ RESPONSIVE ═══════════════ */
@media (max-width: 900px) {
  .qa-layout {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(140px, 30%) 1fr;
  }
  .qa-sidebar {
    max-height: 240px;
  }
}
</style>
