import { useState, type FormEvent } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'
import { login, isValidEmail, type AuthUser } from '../services/auth'
import { LeafIcon } from '../components/icons'

interface LoginScreenProps {
  onLogin: (user: AuthUser) => void
  onGoSignup: () => void
}

export function LoginScreen({ onLogin, onGoSignup }: LoginScreenProps) {
  const { t } = useLanguage()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

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

    setLoading(true)
    try {
      const user = await login(email.trim(), password)
      onLogin(user)
    } catch (err) {
      if (err instanceof Error && err.message === 'invalid-credentials') {
        setError(t.auth.errors.loginFailed)
      } else {
        setError(t.auth.errors.loginFailed)
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

      <h1 className="auth-screen__title">{t.auth.loginTitle}</h1>

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        {error && <ErrorMessage message={error} />}

        <div className="auth-field">
          <label htmlFor="login-email">{t.auth.email}</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            disabled={loading}
            placeholder="farmer@example.com"
          />
        </div>

        <div className="auth-field">
          <label htmlFor="login-password">{t.auth.password}</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            disabled={loading}
            placeholder="••••••"
          />
        </div>

        <Button type="submit" className="auth-form__submit" loading={loading}>
          {loading ? t.auth.loggingIn : t.auth.loginButton}
        </Button>
      </form>

      <p className="auth-switch">
        {t.auth.noAccount}{' '}
        <button type="button" className="auth-switch__link" onClick={onGoSignup} disabled={loading}>
          {t.auth.goSignup}
        </button>
      </p>
    </div>
  )
}
