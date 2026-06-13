<template>
  <div class="markdown-body" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import java from 'highlight.js/lib/languages/java'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import cpp from 'highlight.js/lib/languages/cpp'
import json from 'highlight.js/lib/languages/json'
import bash from 'highlight.js/lib/languages/bash'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import yaml from 'highlight.js/lib/languages/yaml'

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('java', java)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('c', cpp)
hljs.registerLanguage('json', json)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)

marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
  gfm: true
})

const props = defineProps({ content: { type: String, default: '' } })

const renderedHtml = computed(() => {
  if (!props.content) return '<p class="text-muted">No content</p>'
  return marked.parse(props.content)
})
</script>

<style>
/* Override highlight.js theme colors for dark mode */
.markdown-body .hljs-keyword { color: #c792ea; }
.markdown-body .hljs-string { color: #c3e88d; }
.markdown-body .hljs-number { color: #f78c6c; }
.markdown-body .hljs-comment { color: #546e7a; font-style: italic; }
.markdown-body .hljs-function { color: #82aaff; }
.markdown-body .hljs-title { color: #82aaff; }
.markdown-body .hljs-type { color: #ffcb6b; }
.markdown-body .hljs-built_in { color: #ffcb6b; }
.markdown-body .hljs-attr { color: #c792ea; }
.markdown-body .hljs-params { color: #eeffff; }
.markdown-body .hljs-meta { color: #89ddff; }
.markdown-body .hljs-literal { color: #f78c6c; }
.markdown-body .hljs-property { color: #80cbc4; }

.markdown-body h1 { font-size: 2rem; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border-medium); }
.markdown-body h2 { font-size: 1.5rem; margin: 28px 0 12px; }
.markdown-body h3 { font-size: 1.2rem; margin: 20px 0 10px; color: var(--neon-cyan); }
.markdown-body p { margin: 8px 0; line-height: 1.7; }
.markdown-body ul, .markdown-body ol { padding-left: 24px; margin: 8px 0; }
.markdown-body li { margin: 4px 0; }
.markdown-body blockquote {
  border-left: 3px solid var(--neon-cyan);
  padding: 8px 16px;
  margin: 12px 0;
  background: var(--neon-cyan-10);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-secondary);
}
.markdown-body hr { border: none; border-top: 1px solid var(--border-medium); margin: 24px 0; }
.markdown-body strong { color: var(--neon-lime); font-weight: 600; }
.markdown-body a { color: var(--neon-cyan); }
.markdown-body table { width: 100%; border-collapse: collapse; margin: 12px 0; }
.markdown-body th, .markdown-body td { padding: 8px 12px; border: 1px solid var(--border-medium); text-align: left; }
.markdown-body th { background: var(--bg-elevated); font-weight: 600; }
.markdown-body img { max-width: 100%; border-radius: var(--radius-sm); }
</style>
