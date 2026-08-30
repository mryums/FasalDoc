import { useLanguage } from '../i18n/LanguageContext'
import type { Language } from '../i18n/translations'

const OPTIONS: { value: Language; label: string }[] = [
  { value: 'en', label: 'EN' },
  { value: 'ur', label: 'اردو' },
  { value: 'rom', label: 'Roman' },
]

export function LanguageToggle() {
  const { lang, setLang } = useLanguage()
  return (
    <div className="lang-toggle" role="group" aria-label="Language">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`lang-toggle__btn ${lang === opt.value ? 'lang-toggle__btn--active' : ''}`}
          aria-pressed={lang === opt.value}
          onClick={() => setLang(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
