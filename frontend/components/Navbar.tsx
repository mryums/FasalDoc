import { LeafIcon } from './icons'
import { LanguageToggle } from './LanguageToggle'
import { useLanguage } from '../i18n/LanguageContext'

interface NavbarProps {
  showNewDiagnosis: boolean
  onNewDiagnosis: () => void
}

export function Navbar({ showNewDiagnosis, onNewDiagnosis }: NavbarProps) {
  const { t } = useLanguage()
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <div className="navbar__brand">
          <span className="navbar__logo">
            <LeafIcon size={22} />
          </span>
          <span className="navbar__name">{t.appName}</span>
        </div>
        <div className="navbar__actions">
          {showNewDiagnosis && (
            <button type="button" className="navbar__reset" onClick={onNewDiagnosis}>
              {t.nav.newDiagnosis}
            </button>
          )}
          <LanguageToggle />
        </div>
      </div>
    </header>
  )
}
