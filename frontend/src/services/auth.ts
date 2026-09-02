/**
 * Frontend authentication service for FasalDoc.
 *
 * No backend auth endpoints exist yet (Member 2). This module provides
 * a complete frontend auth flow using localStorage for session persistence.
 * When real auth endpoints are available, replace the mock implementations
 * of `login` and `signup` with fetch calls to the backend.
 */

const SESSION_KEY = 'fasaldoc-session'

export interface AuthUser {
  name: string
  email: string
}

export function isAuthenticated(): boolean {
  return getCurrentUser() !== null
}

export function getCurrentUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as AuthUser
    if (parsed && typeof parsed.name === 'string' && typeof parsed.email === 'string') {
      return parsed
    }
    return null
  } catch {
    return null
  }
}

function saveSession(user: AuthUser): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user))
}

export function logout(): void {
  localStorage.removeItem(SESSION_KEY)
}

/**
 * Validate an email address format.
 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/**
 * Login — currently mock-based. When backend auth is available,
 * replace the body with a real POST to the auth endpoint.
 */
export async function login(email: string, _password: string): Promise<AuthUser> {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 600))

  // Check if a matching account was previously "signed up"
  const accountsKey = 'fasaldoc-accounts'
  try {
    const raw = localStorage.getItem(accountsKey)
    if (raw) {
      const accounts = JSON.parse(raw) as Array<{ name: string; email: string; password: string }>
      const found = accounts.find(
        (a) => a.email.toLowerCase() === email.toLowerCase(),
      )
      if (found && found.password === _password) {
        const user = { name: found.name, email: found.email }
        saveSession(user)
        return user
      }
      if (found) {
        throw new Error('invalid-credentials')
      }
    }
  } catch (err) {
    if (err instanceof Error && err.message === 'invalid-credentials') {
      throw err
    }
    // storage issues — fall through to mock login
  }

  // Fallback mock login for demo: any valid email + password >= 6 chars works
  const user: AuthUser = {
    name: email.split('@')[0],
    email,
  }
  saveSession(user)
  return user
}

/**
 * Signup — currently mock-based. When backend auth is available,
 * replace the body with a real POST to the auth endpoint.
 */
export async function signup(
  name: string,
  email: string,
  password: string,
): Promise<AuthUser> {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 600))

  // Store in mock accounts for later login
  const accountsKey = 'fasaldoc-accounts'
  try {
    const raw = localStorage.getItem(accountsKey)
    const accounts: Array<{ name: string; email: string; password: string }> = raw
      ? JSON.parse(raw)
      : []
    // Check for duplicate
    if (accounts.some((a) => a.email.toLowerCase() === email.toLowerCase())) {
      throw new Error('email-exists')
    }
    accounts.push({ name, email, password })
    localStorage.setItem(accountsKey, JSON.stringify(accounts))
  } catch (err) {
    if (err instanceof Error && err.message === 'email-exists') throw err
    // storage issues — continue with session only
  }

  const user: AuthUser = { name, email }
  saveSession(user)
  return user
}
