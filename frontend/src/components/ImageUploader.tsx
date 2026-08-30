import { useRef, useState, type ChangeEvent } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { CameraIcon, TrashIcon, UploadIcon } from './icons'

interface ImageUploaderProps {
  file: File | null
  previewUrl: string | null
  disabled?: boolean
  onSelect: (file: File) => void
  onRemove: () => void
}

export function ImageUploader({
  file,
  previewUrl,
  disabled,
  onSelect,
  onRemove,
}: ImageUploaderProps) {
  const { t } = useLanguage()
  const galleryInput = useRef<HTMLInputElement>(null)
  const cameraInput = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  function handlePicked(e: ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0]
    if (picked) onSelect(picked)
    e.target.value = ''
  }

  const accept = 'image/jpeg,image/png,image/webp'

  if (file && previewUrl) {
    return (
      <div className="uploader uploader--filled">
        <img src={previewUrl} alt={t.result.imageLabel} className="uploader__preview" />
        <div className="uploader__meta">
          <span className="uploader__filename">{file.name}</span>
          <span className="uploader__filesize">{formatSize(file.size)}</span>
        </div>
        <div className="uploader__actions">
          <button
            type="button"
            className="uploader__change"
            onClick={() => galleryInput.current?.click()}
            disabled={disabled}
          >
            <UploadIcon size={16} />
            {t.upload.changePhoto}
          </button>
          <button
            type="button"
            className="uploader__remove"
            onClick={onRemove}
            disabled={disabled}
            aria-label={t.upload.removePhoto}
          >
            <TrashIcon size={16} />
            {t.upload.removePhoto}
          </button>
        </div>
        <input
          ref={galleryInput}
          type="file"
          accept={accept}
          onChange={handlePicked}
          className="visually-hidden-input"
          tabIndex={-1}
          aria-label={t.upload.choosePhoto}
        />
      </div>
    )
  }

  return (
    <div
      className={`uploader ${dragOver ? 'uploader--dragover' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const dropped = e.dataTransfer.files?.[0]
        if (dropped) onSelect(dropped)
      }}
    >
      <button
        type="button"
        className="uploader__empty"
        onClick={() => galleryInput.current?.click()}
        disabled={disabled}
      >
        <UploadIcon size={34} className="uploader__empty-icon" />
        <span className="uploader__empty-label">{t.upload.dropPhoto}</span>
        <span className="uploader__formats">{t.upload.formatsNote}</span>
      </button>
      <div className="uploader__buttons">
        <button
          type="button"
          className="uploader__pick"
          onClick={() => galleryInput.current?.click()}
          disabled={disabled}
        >
          <UploadIcon size={18} />
          {t.upload.choosePhoto}
        </button>
        <button
          type="button"
          className="uploader__pick"
          onClick={() => cameraInput.current?.click()}
          disabled={disabled}
        >
          <CameraIcon size={18} />
          {t.upload.useCamera}
        </button>
      </div>
      <input
        ref={galleryInput}
        type="file"
        accept={accept}
        onChange={handlePicked}
        className="visually-hidden-input"
        tabIndex={-1}
        aria-label={t.upload.choosePhoto}
      />
      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handlePicked}
        className="visually-hidden-input"
        tabIndex={-1}
        aria-label={t.upload.useCamera}
      />
    </div>
  )
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${Math.ceil(bytes / 1024)} KB`
}
