import { LeafIcon, LogoutIcon } from './icons'
import { LanguageToggle } from './LanguageToggle'
import { useLanguage } from '../i18n/LanguageContext'

interface NavbarProps {
  showNewDiagnosis: boolean
  showLogout: boolean
  showDashboard: boolean
  onNewDiagnosis: () => void
  onLogout: () => void
  onDashboard: () => void
}

export function Navbar({
  showNewDiagnosis,
  showLogout,
  showDashboard,
  onNewDiagnosis,
  onLogout,
  onDashboard,
}: NavbarProps) {
  const { t } = useLanguage()
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <div className="navbar__brand">
          <button
            type="button"
            className="navbar__brand-btn"
            onClick={showDashboard ? onDashboard : undefined}
            aria-label={t.appName}
          >
            <span className="navbar__logo">
              <LeafIcon size={22} />
            </span>
            <span className="navbar__name">{t.appName}</span>
          </button>
        </div>
        <div className="navbar__actions">
          {showNewDiagnosis && (
            <button type="button" className="navbar__reset" onClick={onNewDiagnosis}>
              {t.nav.newDiagnosis}
            </button>
          )}
          <LanguageToggle />
          {showLogout && (
            <button
              type="button"
              className="navbar__logout"
              onClick={onLogout}
              aria-label={t.nav.logout}
            >
              <LogoutIcon size={18} />
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
