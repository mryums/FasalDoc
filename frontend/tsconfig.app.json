import { useLanguage } from '../i18n/LanguageContext'
import { ImageUploader } from '../components/ImageUploader'
import { QuestionInput } from '../components/QuestionInput'
import { Button } from '../components/Button'
import { ErrorMessage } from '../components/ErrorMessage'

interface UploadScreenProps {
  file: File | null
  previewUrl: string | null
  question: string
  error: string | null
  onPickFile: (file: File) => void
  onRemoveFile: () => void
  onQuestionChange: (value: string) => void
  onDiagnose: () => void
}

export function UploadScreen({
  file,
  previewUrl,
  question,
  error,
  onPickFile,
  onRemoveFile,
  onQuestionChange,
  onDiagnose,
}: UploadScreenProps) {
  const { t } = useLanguage()

  return (
    <div className="screen upload-screen">
      <h1 className="screen__title">{t.upload.title}</h1>
      <p className="screen__subtitle">{t.upload.subtitle}</p>

      <ImageUploader
        file={file}
        previewUrl={previewUrl}
        onSelect={onPickFile}
        onRemove={onRemoveFile}
      />

      <div className="field">
        <label className="field__label" htmlFor="farmer-question">
          {t.upload.questionLabel}
        </label>
        <QuestionInput
          id="farmer-question"
          value={question}
          onChange={onQuestionChange}
        />
      </div>

      {error && <ErrorMessage message={error} />}

      <Button className="upload-screen__submit" onClick={onDiagnose}>
        {t.upload.diagnose}
      </Button>
    </div>
  )
}
