/**
 * ResultScreen render contract — one diagnosis response must produce exactly
 * ONE diagnosis section, ONE confidence section, ONE advice section and ONE
 * advice text, all in the selected language only.
 *
 * This is a real render test: it runs the actual component tree through Vite's
 * SSR pipeline + react-dom/server, so it catches duplicated/multi-language
 * blocks that source-grep tests cannot see. No network, no backend.
 *
 *   node scripts/render_contract.mjs        (exit 0 = contract holds)
 */
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'
import { fileURLToPath } from 'node:url'
import React from 'react'

// Always run against the frontend project, whatever the shell's cwd is.
const projectRoot = fileURLToPath(new URL('..', import.meta.url))

const URDU = /[\u0600-\u06FF]/

// Mirrors a real /diagnose payload shape (backend contract, three languages).
const PAYLOADS = {
  ur: {
    filename: 'tomato_h.jpeg',
    diagnosis: 'Healthy',
    diagnosis_localized: 'ٹماٹر صحت مند',
    confidence: 0.85,
    advice:
      'آپ کے ٹماٹر کے پودے بالکل صحت مند ہیں اور ان میں کسی بیماری کے آثار نہیں پائے گئے۔',
    needs_expert: false,
    error: null,
  },
  rom: {
    filename: 'tomato_h.jpeg',
    diagnosis: 'Healthy',
    diagnosis_localized: 'Tamatar bilkul sehatmand hai',
    confidence: 0.85,
    advice:
      'Aap ka tamatar ka paudha bilkul theek aur sehatmand hai, is par kisi bemari ke asraat nahi.',
    needs_expert: false,
    error: null,
  },
  en: {
    filename: 'tomato_h.jpeg',
    diagnosis: 'Healthy',
    diagnosis_localized: '',
    confidence: 0.85,
    advice:
      "Your tomato plant looks healthy - don't over-water it & keep the soil drained.",
    needs_expert: false,
    error: null,
  },
}

const storageFor = (lang) => ({
  getItem: (k) => (k === 'fasaldoc-lang' ? lang : null),
  setItem: () => {},
  removeItem: () => {},
})

const textOf = (html) =>
  html
    .replace(/<svg[\s\S]*?<\/svg>/g, '')
    .replace(/<[^>]+>/g, '\u0000')
    .split('\u0000')
    // react-dom escapes entities in the markup; compare against the raw API
    // strings, so unescape first (otherwise an advice containing ' or & would
    // look different from the payload it came from).
    .map((s) =>
      s
        .replace(/&#x27;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .trim(),
    )
    .filter(Boolean)

const failures = []
const check = (label, ok, detail = '') => {
  if (!ok) failures.push(`${label}${detail ? ` — ${detail}` : ''}`)
  console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${label}${detail ? ` (${detail})` : ''}`)
}

const vite = await createServer({
  root: projectRoot,
  logLevel: 'error',
  server: { middlewareMode: true },
})

try {
  const { LanguageProvider } = await vite.ssrLoadModule('/src/i18n/LanguageContext.tsx')
  const { ResultScreen } = await vite.ssrLoadModule('/src/pages/ResultScreen.tsx')

  for (const [lang, payload] of Object.entries(PAYLOADS)) {
    globalThis.localStorage = storageFor(lang)
    const html = renderToStaticMarkup(
      React.createElement(
        LanguageProvider,
        null,
        React.createElement(ResultScreen, {
          diagnosis: payload,
          error: null,
          previewUrl: null,
          onAskFollowup: () => {},
          onNewDiagnosis: () => {},
          onRetry: () => {},
        }),
      ),
    )
    const count = (needle) => html.split(needle).length - 1
    const visible = textOf(html)
    const allText = visible.join(' ')
    const urduElsewhere = visible.filter((t) => URDU.test(t))

    console.log(`\n===== ${lang} =====`)
    check('1 result screen', count('class="screen result"') === 1, `found ${count('class="screen result"')}`)
    check('1 diagnosis heading', count('diagnosis-card__name') === 1, `found ${count('diagnosis-card__name')}`)
    check('1 confidence section', count('class="confidence ') === 1, `found ${count('class="confidence ')}`)
    check('1 advice section', count('class="card advice-card"') === 1, `found ${count('class="card advice-card"')}`)
    check('1 advice text element', count('advice-card__text') === 1, `found ${count('advice-card__text')}`)
    check(
      'advice rendered verbatim, exactly once',
      visible.filter((t) => t === payload.advice).length === 1,
      `found ${visible.filter((t) => t === payload.advice).length}`,
    )
    // The canonical English key must never replace the localized label in ur/rom.
    if (lang === 'ur' || lang === 'rom') {
      check(
        'canonical English diagnosis not displayed',
        !visible.some((t) => t === payload.diagnosis),
      )
    }
    if (lang === 'ur') {
      check('urdu script rendered', URDU.test(allText))
      check('no latin-only UI card titles', !/>\s*(Recommended Action|Confidence|Possible Problem)\s*</.test(html))
    } else {
      check(`zero urdu chars in ${lang} render`, urduElsewhere.length === 0, urduElsewhere[0]?.slice(0, 60) ?? '')
      check('no urdu UI titles', !/تجویز|یقین کی سطح|ممكنہ/.test(html))
    }
  }
} finally {
  await vite.close()
}

console.log(`\n${failures.length === 0 ? 'CONTRACT OK' : `CONTRACT VIOLATIONS: ${failures.length}`}`)
failures.forEach((f) => console.log(` - ${f}`))
process.exit(failures.length === 0 ? 0 : 1)
