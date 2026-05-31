<template>
  <div class="app-container">
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow-top"></div>
    <div class="bg-glow bg-glow-bottom"></div>
    <NavBar />
    <main class="main-content">
      <router-view v-slot="{ Component, route }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import NavBar from '@/components/NavBar.vue'
</script>

<style>
/* ═══════════════════════════════════════════════
   PROJECT HELPER — NEON CYBERPUNK DESIGN SYSTEM
   Based on UI/UX Pro Max: Dark Mode + Glassmorphism
   ═══════════════════════════════════════════════ */

/* ===== CSS Custom Properties ===== */
:root {
  /* Depth layers */
  --bg-abyss: #030712;
  --bg-deep: #060b1a;
  --bg-surface: #0b1121;
  --bg-elevated: #111b33;
  --bg-field: #0a1226;

  /* Neon accents — multi-color cyberpunk */
  --neon-cyan: #00e5ff;
  --neon-magenta: #e040fb;
  --neon-lime: #76ff03;
  --neon-amber: #ffab00;
  --neon-coral: #ff5252;

  /* Dimmed accent variants */
  --neon-cyan-10: rgba(0, 229, 255, 0.10);
  --neon-cyan-15: rgba(0, 229, 255, 0.15);
  --neon-cyan-25: rgba(0, 229, 255, 0.25);
  --neon-magenta-10: rgba(224, 64, 251, 0.10);
  --neon-magenta-15: rgba(224, 64, 251, 0.15);

  /* Gradients */
  --gradient-hero: linear-gradient(135deg, #00e5ff 0%, #e040fb 50%, #76ff03 100%);
  --gradient-card: linear-gradient(160deg, rgba(17, 27, 51, 0.85) 0%, rgba(11, 17, 33, 0.95) 100%);
  --gradient-btn: linear-gradient(135deg, #00e5ff 0%, #e040fb 100%);
  --gradient-border: linear-gradient(135deg, rgba(0, 229, 255, 0.4), rgba(224, 64, 251, 0.4), rgba(0, 229, 255, 0.1));

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-medium: rgba(255, 255, 255, 0.10);
  --border-glow: rgba(0, 229, 255, 0.20);

  /* Text */
  --text-primary: #f0f4ff;
  --text-secondary: #8899bb;
  --text-muted: #556688;
  --text-accent: #00e5ff;

  /* Shadows */
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
  --shadow-glow-cyan: 0 0 30px rgba(0, 229, 255, 0.12), 0 0 60px rgba(0, 229, 255, 0.04);
  --shadow-glow-magenta: 0 0 30px rgba(224, 64, 251, 0.12), 0 0 60px rgba(224, 64, 251, 0.04);

  /* Radii */
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --radius-full: 9999px;

  /* Typography */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  --font-display: 'Inter', system-ui, sans-serif;

  /* Animation */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-spring: cubic-bezier(0.22, 1.2, 0.36, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;

  /* Spacing (8px rhythm) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}

/* ===== Reset ===== */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-abyss);
  color: var(--text-primary);
  line-height: 1.65;
  min-height: 100vh;
  overflow-x: hidden;
}

#app { position: relative; z-index: 1; }

/* ═══════════════════════════════════════════════
   ANIMATED BACKGROUND
   ═══════════════════════════════════════════════ */

.bg-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 229, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 229, 255, 0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 80% 60% at 50% 30%, black 30%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.bg-glow {
  position: fixed;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
  pointer-events: none;
  z-index: 0;
}

.bg-glow-top {
  width: 700px;
  height: 500px;
  background: var(--neon-cyan);
  top: -200px;
  left: 50%;
  transform: translateX(-50%);
  animation: glowPulse 8s ease-in-out infinite;
}

.bg-glow-bottom {
  width: 500px;
  height: 400px;
  background: var(--neon-magenta);
  bottom: -150px;
  right: -100px;
  animation: glowPulse 8s ease-in-out 4s infinite;
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.12; transform: scale(1); }
  50% { opacity: 0.20; transform: scale(1.1); }
}

/* ═══════════════════════════════════════════════
   LAYOUT
   ═══════════════════════════════════════════════ */

.app-container { min-height: 100vh; display: flex; flex-direction: column; }

.main-content {
  flex: 1;
  padding: var(--space-6);
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* ═══════════════════════════════════════════════
   ACCESSIBILITY
   ═══════════════════════════════════════════════ */

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

:focus-visible {
  outline: 2px solid var(--neon-cyan);
  outline-offset: 3px;
  border-radius: 4px;
}

/* ═══════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════ */

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-medium); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ═══════════════════════════════════════════════
   TYPOGRAPHY
   ═══════════════════════════════════════════════ */

h1 { font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 800; letter-spacing: -0.03em; line-height: 1.15; }
h2 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.3; }
h3 { font-size: 1.15rem; font-weight: 600; line-height: 1.4; }
a { color: var(--text-accent); text-decoration: none; transition: color var(--duration-fast); }
a:hover { color: var(--neon-lime); }

/* ═══════════════════════════════════════════════
   GLASS CARD (Glassmorphism)
   ═══════════════════════════════════════════════ */

.glass-card {
  background: var(--gradient-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow-card);
  transition: border-color var(--duration-normal), box-shadow var(--duration-normal);
  position: relative;
  overflow: hidden;
}

.glass-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: var(--gradient-border);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask-composite: xor;
  opacity: 0;
  transition: opacity var(--duration-normal);
  pointer-events: none;
}

.glass-card:hover::before { opacity: 1; }
.glass-card:hover {
  border-color: var(--border-glow);
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
}

/* ═══════════════════════════════════════════════
   BUTTONS
   ═══════════════════════════════════════════════ */

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: 12px 28px;
  border: none;
  border-radius: var(--radius-full);
  font-family: var(--font-sans);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out-expo);
  text-decoration: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  min-height: 44px;
  letter-spacing: 0.01em;
  position: relative;
  overflow: hidden;
}

.btn:disabled { opacity: 0.4; cursor: not-allowed; pointer-events: none; }

/* Primary — neon gradient */
.btn-primary {
  background: var(--gradient-btn);
  color: #fff;
  box-shadow: 0 4px 20px rgba(0, 229, 255, 0.25);
}

.btn-primary::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 30px rgba(0, 229, 255, 0.4), 0 0 0 1px rgba(0, 229, 255, 0.2) inset;
  transform: translateY(-2px);
}
.btn-primary:hover:not(:disabled)::after { transform: translateX(100%); }
.btn-primary:active:not(:disabled) { transform: translateY(0) scale(0.98); }

/* Secondary — ghost border */
.btn-secondary {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--neon-cyan);
  background: var(--neon-cyan-10);
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.08);
}

/* Ghost */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  padding: 8px 16px;
}

.btn-ghost:hover:not(:disabled) {
  color: var(--text-primary);
  background: rgba(255,255,255,0.04);
}

/* ═══════════════════════════════════════════════
   INPUTS
   ═══════════════════════════════════════════════ */

.input-field {
  width: 100%;
  padding: 14px 18px;
  background: var(--bg-field);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 0.95rem;
  transition: all var(--duration-normal) var(--ease-out-expo);
  outline: none;
  line-height: 1.5;
}

.input-field::placeholder { color: var(--text-muted); }
.input-field:hover { border-color: var(--border-glow); }
.input-field:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 0 3px var(--neon-cyan-15), 0 0 20px rgba(0, 229, 255, 0.06);
}

/* ═══════════════════════════════════════════════
   BADGES
   ═══════════════════════════════════════════════ */

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 14px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.badge-cyan { background: var(--neon-cyan-10); color: var(--neon-cyan); border: 1px solid var(--neon-cyan-25); }
.badge-magenta { background: var(--neon-magenta-10); color: var(--neon-magenta); border: 1px solid rgba(224, 64, 251, 0.25); }
.badge-lime { background: rgba(118, 255, 3, 0.10); color: var(--neon-lime); border: 1px solid rgba(118, 255, 3, 0.25); }

/* ═══════════════════════════════════════════════
   CODE HIGHLIGHTING
   ═══════════════════════════════════════════════ */

pre {
  background: #060b1a !important;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-md);
  padding: 20px !important;
  overflow-x: auto;
  font-family: var(--font-mono) !important;
  font-size: 0.84rem !important;
  line-height: 1.65 !important;
  margin: 16px 0;
  tab-size: 4;
}

code { font-family: var(--font-mono); font-size: 0.88em; }
:not(pre) > code {
  background: var(--bg-elevated);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--neon-cyan);
  border: 1px solid var(--border-subtle);
}

/* ═══════════════════════════════════════════════
   ROUTE TRANSITIONS
   ═══════════════════════════════════════════════ */

.page-fade-enter-active {
  transition: opacity var(--duration-normal) var(--ease-out-expo),
              transform var(--duration-normal) var(--ease-out-expo);
}
.page-fade-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.page-fade-enter-from { opacity: 0; transform: translateY(16px) scale(0.99); }
.page-fade-leave-to { opacity: 0; transform: translateY(-8px); }

/* ═══════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════ */

@media (max-width: 768px) {
  .main-content { padding: var(--space-4); }
  .bg-glow-top { width: 400px; height: 300px; top: -150px; }
  .bg-glow-bottom { width: 300px; height: 250px; bottom: -100px; }
}
</style>
