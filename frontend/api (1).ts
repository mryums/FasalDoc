import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/Button'
import { UploadIcon, LeafIcon, ShieldIcon } from '../components/icons'
import { agricultureData } from '../data/agriculture'
import type { Translation } from '../i18n/translations'

interface HomeScreenProps {
  onStart: () => void
}

function steps(t: Translation) {
  return [
    { icon: <UploadIcon size={22} />, title: t.home.step1Title, text: t.home.step1Text },
    { icon: <LeafIcon size={22} />, title: t.home.step2Title, text: t.home.step2Text },
    { icon: <ShieldIcon size={22} />, title: t.home.step3Title, text: t.home.step3Text },
  ]
}

export function HomeScreen({ onStart }: HomeScreenProps) {
  const { t } = useLanguage()

  return (
    <div className="screen home">
      <section className="hero">
        <div className="hero__text">
          <h1 className="hero__headline">{t.home.headline}</h1>
          <p className="hero__subtext">{t.home.subtext}</p>
          <Button onClick={onStart} className="hero__cta">
            <UploadIcon size={20} />
            {t.home.cta}
          </Button>
          <p className="hero__langs">{t.home.languagesNote}</p>
        </div>
        <img
          src="/images/hero.png"
          alt=""
          className="hero__image"
          width={768}
          height={512}
        />
      </section>

      <section className="steps" aria-label="How FasalDoc works">
        {steps(t).map((step, i) => (
          <div className="step-card" key={i}>
            <div className="step-card__num" aria-hidden>
              {i + 1}
            </div>
            <div className="step-card__icon">{step.icon}</div>
            <h2 className="step-card__title">{step.title}</h2>
            <p className="step-card__text">{step.text}</p>
          </div>
        ))}
      </section>

      {agricultureData.supportedCrops.length > 0 && (
        <section className="crops">
          {agricultureData.supportedCrops.map((crop) => (
            <span className="crops__chip" key={crop.english}>
              {crop.urdu ?? crop.english}
            </span>
          ))}
        </section>
      )}
    </div>
  )
}
