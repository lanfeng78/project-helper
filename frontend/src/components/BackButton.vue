<template>
  <button class="back-btn" @click="goBack" :aria-label="label">
    <span class="back-arrow" aria-hidden="true">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="19" y1="12" x2="5" y2="12"/>
        <polyline points="12 19 5 12 12 5"/>
      </svg>
    </span>
    <span class="back-label">{{ label }}</span>
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  label: { type: String, default: '返回' },
  fallback: { type: String, default: '/' }
})

const router = useRouter()

function goBack() {
  // history.length is at least 1 even on the first page, so use 1 as the floor.
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push(props.fallback)
  }
}
</script>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 8px 12px;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary, #8899bb);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.06), rgba(224, 64, 251, 0.06));
  border: 1px solid var(--border-medium, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-full, 9999px);
  cursor: pointer;
  transition:
    color 200ms ease,
    border-color 200ms ease,
    transform 200ms ease,
    box-shadow 200ms ease,
    background 200ms ease;
}
.back-btn:hover {
  color: var(--neon-cyan, #00e5ff);
  border-color: var(--neon-cyan, #00e5ff);
  transform: translateX(-3px);
  box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.25), 0 8px 24px -10px rgba(0, 229, 255, 0.4);
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.12), rgba(224, 64, 251, 0.08));
}
.back-btn:focus-visible {
  outline: 2px solid var(--neon-cyan, #00e5ff);
  outline-offset: 3px;
}
.back-btn:active {
  transform: translateX(-1px) scale(0.98);
}

.back-arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  transition: transform 200ms ease;
}
.back-btn:hover .back-arrow { transform: translateX(-2px); }

.back-label { line-height: 1; }

@media (prefers-reduced-motion: reduce) {
  .back-btn, .back-arrow { transition: none; }
  .back-btn:hover { transform: none; }
  .back-btn:hover .back-arrow { transform: none; }
}
</style>
