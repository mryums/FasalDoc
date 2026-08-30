import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { translations, type Language, type Translation } from './translations'

const STORAGE_KEY = 'fasaldoc-lang'

interface LanguageContextValue {
  lang: Language
  t: Translation
  dir: 'ltr' | 'rtl'
  setLang: (lang: Language) => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

function loadInitialLanguage(): Language {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'en' || saved === 'ur' || saved === 'rom') return saved
  } catch {
    // storage unavailable — fall through to default
  }
  return 'en'
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(loadInitialLanguage)

  const setLang = useCallback((next: Language) => {
    setLangState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // non-fatal: language just won't persist
    }
  }, [])

  const dir: 'ltr' | 'rtl' = lang === 'ur' ? 'rtl' : 'ltr'

  useEffect(() => {
    document.documentElement.lang = lang === 'rom' ? 'ur-Latn' : lang
    document.documentElement.dir = dir
    document.documentElement.classList.toggle('lang-ur', lang === 'ur')
    document.documentElement.classList.toggle('lang-rom', lang === 'rom')
  }, [lang, dir])

  const value = useMemo(
    () => ({ lang, t: translations[lang], dir, setLang }),
    [lang, dir, setLang],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider')
  return ctx
}
