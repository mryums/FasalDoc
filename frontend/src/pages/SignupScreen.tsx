import { useState, type FormEvent } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { signup, isValidEmail, type AuthUser } from '../services/auth'
import { LeafIcon } from '../components/icons'

interface SignupScreenProps {
  onSignup: (user: AuthUser) => void
  onGoLogin: () => void
}

export function SignupScreen({ onSignup, onGoLogin }: SignupScreenProps) {
  const { t } = useLanguage()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError(t.auth.errors.nameRequired)
      return
    }
    if (!email.trim()) {
      setError(t.auth.errors.emailRequired)
      return
    }
    if (!isValidEmail(email.trim())) {
      setError(t.auth.errors.invalidEmail)
      return
    }
    if (!password) {
      setError(t.auth.errors.passwordRequired)
      return
    }
    if (password.length < 6) {
      setError(t.auth.errors.passwordShort)
      return
    }
    if (password !== confirmPassword) {
      setError(t.auth.errors.passwordMismatch)
      return
    }

    setLoading(true)
    try {
      const user = await signup(name.trim(), email.trim(), password)
      onSignup(user)
    } catch (err) {
      if (err instanceof Error && err.message === 'email-exists') {
        setError(t.auth.errors.signupFailed)
      } else {
        setError(t.auth.errors.signupFailed)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen auth-screen">
      <div className="auth-screen__brand">
        <span className="auth-screen__logo">
          <LeafIcon size={28} />
        </span>
        <span className="auth-screen__appname">{t.appName}</span>
      </div>

      <h1 className="auth-screen__title">{t.auth.signupTitle}</h1>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {error && <ErrorMessage message={error} />}

        <div className="auth-field">
          <label htmlFor="signup-name">{t.auth.name}</label>
          <input
            id="signup-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="name"
            disabled={loading}
          />
        </div>

        <div className="auth-field">
          <label htmlFor="signup-email">{t.auth.email}</label>
          <input
            id="signup-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            disabled={loading}
            placeholder="farmer@example.com"
          />
        </div>

        <div className="auth-field">
          <label htmlFor="signup-password">{t.auth.password}</label>
          <input
            id="signup-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            disabled={loading}
            placeholder="••••••"
          />
        </div>

        <div className="auth-field">
          <label htmlFor="signup-confirm">{t.auth.confirmPassword}</label>
          <input
            id="signup-confirm"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            disabled={loading}
            placeholder="••••••"
          />
        </div>

        <Button type="submit" className="auth-form__submit" loading={loading}>
          {loading ? t.auth.signingUp : t.auth.signupButton}
        </Button>
      </form>

      <p className="auth-switch">
        {t.auth.hasAccount}{' '}
        <button type="button" className="auth-switch__link" onClick={onGoLogin} disabled={loading}>
          {t.auth.goLogin}
        </button>
      </p>
    </div>
  )
}
