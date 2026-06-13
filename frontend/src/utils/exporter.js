// Shared clipboard + download helpers used by ReportPage and QAPage.
// No dependencies — works on http://localhost (clipboard API requires
// secure context, so a textarea fallback is included for older / non-HTTPS).

export async function copyText(text) {
  if (text == null) return false
  try {
    if (navigator.clipboard && window.isSecureContext !== false) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    /* fall through to legacy path */
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', '')
    ta.style.position = 'fixed'
    ta.style.top = '0'
    ta.style.left = '0'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    ta.setSelectionRange(0, ta.value.length)
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}

export function downloadMarkdown(filename, content) {
  const safe = (filename || 'untitled').toString()
  const finalName = safe.endsWith('.md') ? safe : `${safe}.md`
  const blob = new Blob([content ?? ''], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = finalName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// Strip characters illegal on Windows / unfriendly in URLs, trim, cap length.
export function safeFilename(s) {
  return (s || 'untitled')
    .toString()
    .replace(/[\\/:*?"<>|\r\n\t]+/g, '_')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80) || 'untitled'
}
