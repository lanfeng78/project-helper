<template>
  <div class="app-container">
    <!-- Atmospheric mist: layered radial gradients (the "water wall") -->
    <div class="bg-mist" aria-hidden="true"></div>

    <!-- Geometric line work: rings, diagonals, tick marks -->
    <svg class="bg-frame" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="bgCM" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.7"/>
          <stop offset="100%" stop-color="#e040fb" stop-opacity="0.6"/>
        </linearGradient>
        <linearGradient id="bgCM2" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stop-color="#e040fb" stop-opacity="0.55"/>
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.45"/>
        </linearGradient>
      </defs>
      <!-- Concentric rings, top-right -->
      <g class="bg-rings" transform="translate(1420 -100)">
        <circle r="420" fill="none" stroke="url(#bgCM)"  stroke-width="1"   stroke-dasharray="3 9" opacity="0.45"/>
        <circle r="320" fill="none" stroke="url(#bgCM)"  stroke-width="1"                          opacity="0.32"/>
        <circle r="220" fill="none" stroke="url(#bgCM2)" stroke-width="1"   stroke-dasharray="6 6" opacity="0.50"/>
        <circle r="120" fill="none" stroke="url(#bgCM2)" stroke-width="1.2"                        opacity="0.40"/>
      </g>
      <!-- Sweeping diagonals -->
      <line x1="-120" y1="780" x2="980"  y2="-220" stroke="url(#bgCM)"  stroke-width="1" opacity="0.22"/>
      <line x1="180"  y1="980" x2="1740" y2="-420" stroke="url(#bgCM2)" stroke-width="1" opacity="0.18"/>
      <line x1="-220" y1="540" x2="780"  y2="1280" stroke="url(#bgCM)"  stroke-width="1" opacity="0.20"/>
      <!-- Tick / scale, bottom-left engineering signature -->
      <g class="bg-ticks" transform="translate(80 820)">
        <line x1="0"   y1="0"   x2="200" y2="0"   stroke="#00e5ff" stroke-width="1.6" opacity="0.55"/>
        <line x1="0"   y1="-12" x2="0"   y2="12"  stroke="#00e5ff" stroke-width="1.6" opacity="0.55"/>
        <line x1="100" y1="-8"  x2="100" y2="8"   stroke="#00e5ff" stroke-width="1.2" opacity="0.40"/>
        <line x1="200" y1="-12" x2="200" y2="12"  stroke="#e040fb" stroke-width="1.6" opacity="0.55"/>
      </g>
      <!-- Cross-hair marker, mid-right -->
      <g transform="translate(1320 460)" opacity="0.45">
        <line x1="-30" y1="0" x2="30" y2="0" stroke="#00e5ff" stroke-width="1"/>
        <line x1="0" y1="-30" x2="0" y2="30" stroke="#00e5ff" stroke-width="1"/>
        <circle r="6" fill="none" stroke="#00e5ff" stroke-width="1"/>
      </g>
    </svg>

    <!-- Diagonal scan light -->
    <div class="bg-scan" aria-hidden="true"></div>

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
  /* Depth layers — deep ink with violet bias, never pure black */
  --bg-abyss: #07061a;
  --bg-deep: #0a0822;
  --bg-surface: #0f0d2c;
  --bg-elevated: #15123a;
  --bg-field: #0c0a26;
  --ink-deep: #050316;
  --mist: #b8c5e6;

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
  --gradient-card: linear-gradient(165deg, rgba(21, 18, 58, 0.72) 0%, rgba(10, 8, 34, 0.88) 100%);
  --gradient-btn: linear-gradient(135deg, #00e5ff 0%, #e040fb 100%);
  --gradient-border: linear-gradient(135deg, rgba(0, 229, 255, 0.55), rgba(224, 64, 251, 0.55), rgba(0, 229, 255, 0.12));
  --gradient-stroke: linear-gradient(135deg, rgba(0, 229, 255, 0.35), rgba(224, 64, 251, 0.35));

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-medium: rgba(255, 255, 255, 0.10);
  --border-glow: rgba(0, 229, 255, 0.30);

  /* Text */
  --text-primary: #f0f4ff;
  --text-secondary: #a8b3d6;
  --text-muted: #6b78a3;
  --text-accent: #00e5ff;

  /* Shadows */
  --shadow-card: 0 8px 32px rgba(2, 2, 16, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
  --shadow-glow-cyan: 0 0 30px rgba(0, 229, 255, 0.14), 0 0 60px rgba(0, 229, 255, 0.05);
  --shadow-glow-magenta: 0 0 30px rgba(224, 64, 251, 0.14), 0 0 60px rgba(224, 64, 251, 0.05);

  /* Radii */
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --radius-full: 9999px;

  /* Typography */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
  --font-display: 'JetBrains Mono', 'Inter', system-ui, sans-serif;

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
  background:
    radial-gradient(ellipse 90% 60% at 12% -10%, rgba(0, 229, 255, 0.18) 0%, transparent 55%),
    radial-gradient(ellipse 70% 60% at 100% 110%, rgba(224, 64, 251, 0.18) 0%, transparent 55%),
    radial-gradient(ellipse 60% 50% at 50% 50%, rgba(118, 90, 255, 0.10) 0%, transparent 70%),
    linear-gradient(180deg, #07061a 0%, #0a0822 50%, #0d0726 100%);
  background-attachment: fixed;
  color: var(--text-primary);
  line-height: 1.65;
  min-height: 100vh;
  overflow-x: hidden;
}

#app { position: relative; z-index: 1; }

/* ═══════════════════════════════════════════════
   ATMOSPHERIC BACKGROUND — Deep Wall + Geometry + Scan
   ═══════════════════════════════════════════════ */

/* Layer 1: drifting mist orbs (replaces bg-glow) */
.bg-mist {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(circle 480px at 18% 12%, rgba(0, 229, 255, 0.16),  transparent 70%),
    radial-gradient(circle 520px at 88% 92%, rgba(224, 64, 251, 0.18), transparent 70%),
    radial-gradient(circle 360px at 78% 18%, rgba(118, 90, 255, 0.10), transparent 75%),
    radial-gradient(circle 280px at 16% 78%, rgba(0, 229, 255, 0.08),  transparent 75%);
  filter: blur(8px);
  animation: mistDrift 18s ease-in-out infinite alternate;
}

@keyframes mistDrift {
  0%   { transform: translate3d(0, 0, 0) scale(1); opacity: 0.85; }
  100% { transform: translate3d(-2%, 1.5%, 0) scale(1.04); opacity: 1; }
}

/* Layer 2: SVG line work — bold geometric strokes */
.bg-frame {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  mask-image: radial-gradient(ellipse 95% 90% at 50% 45%, black 30%, transparent 92%);
  -webkit-mask-image: radial-gradient(ellipse 95% 90% at 50% 45%, black 30%, transparent 92%);
}

.bg-frame .bg-rings {
  transform-origin: 1420px -100px;
  animation: ringSpin 60s linear infinite;
}

@keyframes ringSpin {
  to { transform: translate(1420px, -100px) rotate(360deg); }
}

/* Layer 3: diagonal scan light */
.bg-scan {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(
    115deg,
    transparent 38%,
    rgba(0, 229, 255, 0.04) 47%,
    rgba(224, 64, 251, 0.05) 52%,
    transparent 62%
  );
  mix-blend-mode: screen;
  animation: scanSlide 12s ease-in-out infinite;
}

@keyframes scanSlide {
  0%, 100% { transform: translateX(-8%); opacity: 0.8; }
  50%      { transform: translateX(8%);  opacity: 1; }
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
  .bg-mist, .bg-scan, .bg-frame .bg-rings { animation: none !important; }
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
  transition: border-color var(--duration-normal), box-shadow var(--duration-normal), transform var(--duration-normal);
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
  opacity: 0.35;                 /* always-on subtle gradient stroke */
  transition: opacity var(--duration-normal);
  pointer-events: none;
}

.glass-card:hover::before { opacity: 1; }
.glass-card:hover {
  border-color: var(--border-glow);
  box-shadow: var(--shadow-card), var(--shadow-glow-cyan);
  transform: translateY(-2px);
}

/* ═══════════════════════════════════════════════
   SECTION TAGS — engineering signage
   ═══════════════════════════════════════════════ */

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--neon-cyan);
  margin-bottom: var(--space-3);
}
.section-tag::before {
  content: '';
  width: 22px;
  height: 1px;
  background: linear-gradient(90deg, var(--neon-cyan), transparent);
}
.section-tag .num {
  color: var(--text-muted);
  margin-left: auto;
  padding-left: 14px;
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
  background: rgba(3, 7, 18, 0.55);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 20px;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.84rem;
  line-height: 1.65;
  margin: 16px 0;
  tab-size: 4;
  backdrop-filter: blur(8px);
}

/* Plain-text fenced blocks (e.g. directory tree ├── └──) — keep alignment, no extra background */
.markdown-body pre > code.language-text,
.markdown-body pre > code:not([class*="language-"]),
.markdown-body pre > code.hljs.language-plaintext {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.65;
  color: var(--text-primary);
  background: transparent;
  white-space: pre;
  display: block;
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
  .bg-frame { mask-image: radial-gradient(ellipse 110% 100% at 50% 45%, black 30%, transparent 95%); }
}
</style>
