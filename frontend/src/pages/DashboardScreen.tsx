import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/Button'
import {
  CameraIcon,
  UploadIcon,
  MicIcon,
  SproutIcon,
} from '../components/icons'
import { agricultureData } from '../data/agriculture'
import type { AuthUser } from '../services/auth'

interface DashboardScreenProps {
  user: AuthUser
  onUploadPhoto: () => void
  onUseCamera: () => void
  onAskQuestion: () => void
  onVoiceInput: () => void
}

export function DashboardScreen({
  user,
  onUploadPhoto,
  onUseCamera,
  onAskQuestion,
  onVoiceInput,
}: DashboardScreenProps) {
  const { t, lang } = useLanguage()

  const greeting = t.dashboard.greeting.replace('{name}', user.name)

  const actions = [
    {
      icon: <UploadIcon size={26} />,
      title: t.dashboard.uploadPhoto,
      desc: t.dashboard.uploadDesc,
      onClick: onUploadPhoto,
    },
    {
      icon: <CameraIcon size={26} />,
      title: t.dashboard.useCamera,
      desc: t.dashboard.cameraDesc,
      onClick: onUseCamera,
    },
    {
      icon: <SproutIcon size={26} />,
      title: t.dashboard.askQuestion,
      desc: t.dashboard.askDesc,
      onClick: onAskQuestion,
    },
    {
      icon: <MicIcon size={26} />,
      title: t.dashboard.voiceInput,
      desc: t.dashboard.voiceDesc,
      onClick: onVoiceInput,
    },
  ]

  return (
    <div className="screen dashboard">
      <div className="dashboard__greeting">
        <h1 className="dashboard__title">{greeting}</h1>
        <p className="dashboard__subtitle">{t.dashboard.subtitle}</p>
      </div>

      <div className="dashboard__actions">
        {actions.map((action) => (
          <button
            key={action.title}
            type="button"
            className="action-card"
            onClick={action.onClick}
          >
            <div className="action-card__icon">{action.icon}</div>
            <div className="action-card__text">
              <span className="action-card__title">{action.title}</span>
              <span className="action-card__desc">{action.desc}</span>
            </div>
          </button>
        ))}
      </div>

      {agricultureData.supportedCrops.length > 0 && (
        <section className="dashboard__crops">
          <h2 className="dashboard__section-title">{t.dashboard.recentActivity}</h2>
          <div className="crops">
            {agricultureData.supportedCrops.map((crop) => (
              <span className="crops__chip" key={crop.english}>
                {lang === 'ur'
                  ? crop.urdu ?? crop.english
                  : lang === 'rom'
                    ? crop.romanUrdu ?? crop.english
                    : crop.english}
              </span>
            ))}
          </div>
        </section>
      )}

      <div className="dashboard__quick-start">
        <Button onClick={onUploadPhoto} className="dashboard__cta">
          <UploadIcon size={18} />
          {t.dashboard.startDiagnosis}
        </Button>
      </div>
    </div>
  )
}
