<template>
  <div class="progress-container">
    <div class="progress-track">
      <div class="progress-fill" :style="{ width: percent + '%' }">
        <div class="progress-shine"></div>
      </div>
      <div class="progress-glow" :style="{ left: percent + '%' }"></div>
    </div>
    <div class="progress-info">
      <span class="progress-msg">
        <span class="msg-dot" :class="{ active: percent < 100, done: percent >= 100, error: hasError }"></span>
        {{ message }}
      </span>
      <span class="progress-pct">{{ percent }}%</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  percent: { type: Number, default: 0 },
  message: { type: String, default: '' },
  hasError: { type: Boolean, default: false }
})
</script>

<style scoped>
.progress-container { width: 100%; }

.progress-track {
  height: 8px;
  background: var(--bg-field);
  border-radius: var(--radius-full);
  overflow: visible;
  position: relative;
  margin-bottom: var(--space-3);
  border: 1px solid var(--border-subtle);
}

.progress-fill {
  height: 100%;
  background: var(--gradient-btn);
  border-radius: var(--radius-full);
  transition: width 0.6s var(--ease-out-expo);
  position: relative;
  overflow: hidden;
}

.progress-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 40%, transparent 60%);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

.progress-glow {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px; height: 12px;
  background: var(--neon-cyan);
  border-radius: 50%;
  filter: blur(6px);
  opacity: 0.6;
  transition: left 0.6s var(--ease-out-expo);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-msg {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.msg-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  flex-shrink: 0;
}

.msg-dot.active { background: var(--neon-cyan); animation: pulse 1.5s ease-in-out infinite; }
.msg-dot.done { background: var(--neon-lime); }
.msg-dot.error { background: var(--neon-coral); }

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 var(--neon-cyan-25); }
  50% { opacity: 0.5; box-shadow: 0 0 0 6px transparent; }
}

.progress-pct {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--neon-cyan);
  font-family: var(--font-mono);
}
</style>
