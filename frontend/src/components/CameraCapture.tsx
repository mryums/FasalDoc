import { useCallback, useEffect, useRef, useState } from 'react'
import { useLanguage } from '../i18n/LanguageContext'
import { Button } from './Button'
import { CameraIcon, RefreshIcon, XIcon } from './icons'

interface CameraCaptureProps {
  onCapture: (file: File) => void
  onClose: () => void
}

type CameraState = 'loading' | 'live' | 'captured' | 'error' | 'unsupported'

export function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const { t } = useLanguage()
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [state, setState] = useState<CameraState>('loading')
  const [capturedUrl, setCapturedUrl] = useState<string | null>(null)
  const capturedFileRef = useRef<File | null>(null)

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [])

  const startCamera = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setState('unsupported')
      return
    }

    setState('loading')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setState('live')
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setState('error')
      } else if (err instanceof DOMException && err.name === 'NotFoundError') {
        setState('unsupported')
      } else {
        setState('error')
      }
    }
  }, [])

  useEffect(() => {
    startCamera()
    return () => {
      stopStream()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleCapture() {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas || state !== 'live') return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.drawImage(video, 0, 0)

    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const file = new File([blob], `fasaldoc-camera-${Date.now()}.jpg`, {
          type: 'image/jpeg',
        })
        capturedFileRef.current = file
        const url = URL.createObjectURL(blob)
        setCapturedUrl(url)
        setState('captured')
        stopStream()
      },
      'image/jpeg',
      0.92,
    )
  }

  function handleRetake() {
    if (capturedUrl) {
      URL.revokeObjectURL(capturedUrl)
      setCapturedUrl(null)
    }
    capturedFileRef.current = null
    startCamera()
  }

  function handleUsePhoto() {
    if (capturedFileRef.current) {
      onCapture(capturedFileRef.current)
    }
    handleClose()
  }

  function handleClose() {
    stopStream()
    if (capturedUrl) {
      URL.revokeObjectURL(capturedUrl)
    }
    onClose()
  }

  return (
    <div className="camera-modal" role="dialog" aria-label={t.camera.title}>
      <div className="camera-modal__header">
        <span className="camera-modal__title">{t.camera.title}</span>
        <button
          type="button"
          className="camera-modal__close"
          onClick={handleClose}
          aria-label={t.camera.cancel}
        >
          <XIcon size={22} />
        </button>
      </div>

      <div className="camera-modal__viewport">
        <video
          ref={videoRef}
          className="camera-modal__video"
          playsInline
          muted
          autoPlay
          style={{ display: state === 'captured' ? 'none' : 'block' }}
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {capturedUrl && state === 'captured' && (
          <img src={capturedUrl} alt="Captured" className="camera-modal__captured" />
        )}

        {state === 'loading' && (
          <div className="camera-modal__overlay">
            <p className="camera-modal__message">{t.camera.loading}</p>
          </div>
        )}

        {state === 'error' && (
          <div className="camera-modal__overlay">
            <p className="camera-modal__message">{t.camera.permissionDenied}</p>
            <Button variant="secondary" onClick={handleClose}>
              {t.camera.cancel}
            </Button>
          </div>
        )}

        {state === 'unsupported' && (
          <div className="camera-modal__overlay">
            <p className="camera-modal__message">{t.camera.unsupported}</p>
            <Button variant="secondary" onClick={handleClose}>
              {t.camera.cancel}
            </Button>
          </div>
        )}
      </div>

      <div className="camera-modal__controls">
        {state === 'live' && (
          <button
            type="button"
            className="camera-modal__capture"
            onClick={handleCapture}
            aria-label={t.camera.capture}
          >
            <CameraIcon size={28} />
          </button>
        )}

        {state === 'captured' && (
          <div className="camera-modal__actions">
            <Button variant="secondary" onClick={handleRetake}>
              <RefreshIcon size={16} />
              {t.camera.retake}
            </Button>
            <Button onClick={handleUsePhoto}>
              {t.camera.usePhoto}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
