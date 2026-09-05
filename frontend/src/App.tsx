import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { useLanguage } from './i18n/LanguageContext'
import { Navbar } from './components/Navbar'
import { Footer } from './components/Footer'
import { HomeScreen } from './pages/HomeScreen'
import { UploadScreen } from './pages/UploadScreen'
import { AnalyzingScreen } from './pages/AnalyzingScreen'
import { ResultScreen } from './pages/ResultScreen'
import { FollowUpScreen } from './pages/FollowUpScreen'
import { LoginScreen } from './pages/LoginScreen'
import { SignupScreen } from './pages/SignupScreen'
import { DashboardScreen } from './pages/DashboardScreen'
import type { ChatMessageData } from './components/ChatMessage'
import type { DiagnosisResponse } from './types/api'
import {
  ApiError,
  askFollowup,
  diagnoseImage,
  validateImageFile,
  type ImageValidationError,
} from './services/api'
import {
  isAuthenticated,
  getCurrentUser,
  logout as authLogout,
  type AuthUser,
} from './services/auth'

type Screen = 'login' | 'signup' | 'dashboard' | 'home' | 'upload' | 'analyzing' | 'result' | 'followup'

interface FlowState {
  screen: Screen
  file: File | null
  previewUrl: string | null
  question: string
  uploadError: string | null
  diagnosis: DiagnosisResponse | null
  diagnoseError: string | null
  messages: ChatMessageData[]
  sending: boolean
  sendError: string | null
}

type Action =
  | { type: 'go-login' }
  | { type: 'go-signup' }
  | { type: 'go-dashboard' }
  | { type: 'go-home' }
  | { type: 'go-upload' }
  | { type: 'pick-file'; file: File; previewUrl: string }
  | { type: 'pick-file-error'; error: string }
  | { type: 'remove-file' }
  | { type: 'set-question'; value: string }
  | { type: 'start-diagnosis' }
  | { type: 'diagnosis-success'; diagnosis: DiagnosisResponse }
  | { type: 'diagnosis-error'; error: string }
  | { type: 'go-followup' }
  | { type: 'followup-start'; question: string; id: number }
  | { type: 'followup-success'; id: number; answer: string }
  | { type: 'followup-error'; error: string }
  | { type: 'reset' }

const initialState: FlowState = {
  screen: 'login',
  file: null,
  previewUrl: null,
  question: '',
  uploadError: null,
  diagnosis: null,
  diagnoseError: null,
  messages: [],
  sending: false,
  sendError: null,
}

function reducer(state: FlowState, action: Action): FlowState {
  switch (action.type) {
    case 'go-login':
      return { ...initialState, screen: 'login' }
    case 'go-signup':
      return { ...initialState, screen: 'signup' }
    case 'go-dashboard':
      return { ...initialState, screen: 'dashboard' }
    case 'go-home':
      return { ...initialState, screen: 'dashboard' }
    case 'go-upload':
      return { ...initialState, screen: 'upload' }
    case 'pick-file':
      return {
        ...state,
        file: action.file,
        previewUrl: action.previewUrl,
        uploadError: null,
      }
    case 'pick-file-error':
      return { ...state, uploadError: action.error }
    case 'remove-file':
      return { ...state, file: null, previewUrl: null, uploadError: null }
    case 'set-question':
      return { ...state, question: action.value }
    case 'start-diagnosis':
      return { ...state, screen: 'analyzing', diagnoseError: null }
    case 'diagnosis-success':
      return { ...state, screen: 'result', diagnosis: action.diagnosis, diagnoseError: null }
    case 'diagnosis-error':
      return { ...state, screen: 'result', diagnosis: null, diagnoseError: action.error }
    case 'go-followup':
      return { ...state, screen: 'followup', sendError: null }
    case 'followup-start':
      return {
        ...state,
        sending: true,
        sendError: null,
        messages: [
          ...state.messages,
          { id: action.id, role: 'farmer', text: action.question },
        ],
      }
    case 'followup-success':
      return {
        ...state,
        sending: false,
        messages: [
          ...state.messages,
          { id: action.id + 1, role: 'fasaldoc', text: action.answer },
        ],
      }
    case 'followup-error':
      return { ...state, sending: false, sendError: action.error }
    case 'reset':
      return { ...state, screen: 'upload', file: null, previewUrl: null, question: '', uploadError: null, diagnosis: null, diagnoseError: null, messages: [], sending: false, sendError: null }
  }
}

export default function App() {
  const { t } = useLanguage()
  const [state, dispatch] = useReducer(reducer, initialState)
  const [user, setUser] = useState<AuthUser | null>(null)
  const idCounter = useRef(0)
  const diagnosisRan = useRef(false)

  // Check auth on mount
  useEffect(() => {
    if (isAuthenticated()) {
      const currentUser = getCurrentUser()
      setUser(currentUser)
      dispatch({ type: 'go-dashboard' })
    } else {
      dispatch({ type: 'go-login' })
    }
  }, [])

  function handleLogin(loggedInUser: AuthUser) {
    setUser(loggedInUser)
    dispatch({ type: 'go-dashboard' })
  }

  function handleLogout() {
    authLogout()
    setUser(null)
    dispatch({ type: 'go-login' })
  }

  const imageValidationError = useCallback(
    (code: ImageValidationError): string => {
      switch (code) {
        case 'no-image':
          return t.upload.errors.noImage
        case 'invalid-type':
          return t.upload.errors.invalidType
        case 'too-large':
          return t.upload.errors.tooLarge
      }
    },
    [t],
  )

  function handlePickFile(file: File) {
    const problem = validateImageFile(file)
    if (problem) {
      dispatch({ type: 'pick-file-error', error: imageValidationError(problem) })
      return
    }
    dispatch({ type: 'pick-file', file, previewUrl: URL.createObjectURL(file) })
  }

  function handleDiagnose() {
    const problem = validateImageFile(state.file)
    if (problem || !state.file) {
      dispatch({ type: 'pick-file-error', error: imageValidationError(problem ?? 'no-image') })
      return
    }
    diagnosisRan.current = false
    dispatch({ type: 'start-diagnosis' })
  }

  useEffect(() => {
    if (state.screen !== 'analyzing' || diagnosisRan.current || !state.file) return
    diagnosisRan.current = true
    const file = state.file
    const question = state.question

    diagnoseImage(file, question)
      .then((diagnosis) => dispatch({ type: 'diagnosis-success', diagnosis }))
      .catch((err: unknown) =>
        dispatch({ type: 'diagnosis-error', error: diagnoseErrorMessage(err) }),
      )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.screen])

  function diagnoseErrorMessage(err: unknown): string {
    if (err instanceof ApiError) {
      if (err.kind === 'network') return t.errors.network
      if (err.kind === 'validation') return `${t.errors.validationPrefix} ${err.message}`
      return t.errors.server
    }
    return t.errors.server
  }

  function followupErrorMessage(err: unknown): string {
    if (err instanceof ApiError) {
      if (err.kind === 'network') return t.errors.network
      if (err.kind === 'validation') return `${t.errors.validationPrefix} ${err.message}`
    }
    return t.errors.server
  }

  async function handleSendFollowup(question: string) {
    if (state.sending) return
    const id = (idCounter.current += 2)
    dispatch({ type: 'followup-start', question, id })
    try {
      const res = await askFollowup(question)
      dispatch({ type: 'followup-success', id, answer: res.answer })
    } catch (err) {
      dispatch({ type: 'followup-error', error: followupErrorMessage(err) })
    }
  }

  const screen = state.screen
  const isAuthenticatedFlow = screen !== 'login' && screen !== 'signup'

  const prevPreview = useRef<string | null>(null)
  useEffect(() => {
    if (prevPreview.current && prevPreview.current !== state.previewUrl) {
      URL.revokeObjectURL(prevPreview.current)
    }
    prevPreview.current = state.previewUrl
  }, [state.previewUrl])

  return (
    <div className="app-shell">
      <Navbar
        showNewDiagnosis={
          isAuthenticatedFlow && (screen === 'upload' || screen === 'result' || screen === 'followup')
        }
        showLogout={isAuthenticatedFlow}
        showDashboard={isAuthenticatedFlow}
        onNewDiagnosis={() => dispatch({ type: 'reset' })}
        onLogout={handleLogout}
        onDashboard={() => dispatch({ type: 'go-dashboard' })}
      />

      <main className="app-main">
        {screen === 'login' && (
          <LoginScreen
            onLogin={handleLogin}
            onGoSignup={() => dispatch({ type: 'go-signup' })}
          />
        )}

        {screen === 'signup' && (
          <SignupScreen
            onSignup={handleLogin}
            onGoLogin={() => dispatch({ type: 'go-login' })}
          />
        )}

        {screen === 'dashboard' && user && (
          <DashboardScreen
            user={user}
            onUploadPhoto={() => dispatch({ type: 'go-upload' })}
            onUseCamera={() => dispatch({ type: 'go-upload' })}
            onAskQuestion={() => dispatch({ type: 'go-upload' })}
            onVoiceInput={() => dispatch({ type: 'go-upload' })}
          />
        )}

        {screen === 'home' && <HomeScreen onStart={() => dispatch({ type: 'go-upload' })} />}

        {screen === 'upload' && (
          <UploadScreen
            file={state.file}
            previewUrl={state.previewUrl}
            question={state.question}
            error={state.uploadError}
            onPickFile={handlePickFile}
            onRemoveFile={() => dispatch({ type: 'remove-file' })}
            onQuestionChange={(value) => dispatch({ type: 'set-question', value })}
            onDiagnose={handleDiagnose}
          />
        )}

        {screen === 'analyzing' && <AnalyzingScreen previewUrl={state.previewUrl} />}

        {screen === 'result' && (
          <ResultScreen
            diagnosis={state.diagnosis}
            error={state.diagnoseError}
            previewUrl={state.previewUrl}
            onAskFollowup={() => dispatch({ type: 'go-followup' })}
            onNewDiagnosis={() => dispatch({ type: 'reset' })}
            onRetry={() => {
              diagnosisRan.current = false
              dispatch({ type: 'start-diagnosis' })
            }}
          />
        )}

        {screen === 'followup' && state.diagnosis && (
          <FollowUpScreen
            diagnosis={state.diagnosis}
            previewUrl={state.previewUrl}
            messages={state.messages}
            sending={state.sending}
            sendError={state.sendError}
            initialDraft={state.question}
            onSend={handleSendFollowup}
          />
        )}
      </main>

      <Footer />
    </div>
  )
}
