import { useLanguage } from '../i18n/LanguageContext'
import { SproutIcon } from './icons'

export function Footer() {
  const { t } = useLanguage()
  return (
    <footer className="footer">
      <div className="footer__inner">
        <p className="footer__disclaimer">{t.footer.disclaimer}</p>
        <p className="footer__tagline">
          <SproutIcon size={16} />
          {t.footer.builtFor}
        </p>
      </div>
    </footer>
  )
}
