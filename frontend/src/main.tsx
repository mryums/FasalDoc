import { StrictMode } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import App from './App'
import { LanguageProvider } from './i18n/LanguageContext'
import './styles/tokens.css'
import './styles/global.css'

// The container carries the single React root this document is allowed to own.
type RootHost = HTMLElement & { __fasaldocRoot?: Root }

const container = document.getElementById('root')! as RootHost

const tree = (
  <StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </StrictMode>
)

// Idempotent mount — this guard is load-bearing, not cosmetic.
//
// If this module is ever executed a SECOND time in the same document (Vite
// re-importing the entry under a new `?t=` stamp after an HMR update or a
// dev-server restart, dependency re-optimisation, or a browser extension
// injecting the entry script twice) a fresh `createRoot()` does NOT replace the
// existing tree — it appends another fully independent tree into #root. Each
// tree owns its own LanguageProvider state (frozen to the language selected at
// its own mount time) and its own reducer state, so the farmer sees the same
// diagnosis rendered once per language: Urdu + English + Roman Urdu blocks
// stacked on one page, with the advice repeated. Reusing the stored root turns
// any re-execution into a plain re-render of the ONE tree.
if (!container.__fasaldocRoot) {
  container.__fasaldocRoot = createRoot(container)
}

container.__fasaldocRoot.render(tree)
