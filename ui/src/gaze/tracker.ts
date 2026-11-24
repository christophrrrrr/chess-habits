// Webcam face tracking with MediaPipe Face Landmarker (Apache-2.0), entirely in the browser.
// The video never leaves the page: only landmark coordinates are used, and nothing is sent to
// a server. The library and model are loaded only when the player opens the gaze page.
import type { Point } from './model'

const VERSION = '1.2.3' // keep in sync with package.json
const WASM = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${VERSION}/wasm`
const MODEL =
  'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

export interface Tracker {
  video: HTMLVideoElement
  stop: () => void
}

/** Starts the camera and calls onFrame with the face landmarks of every video frame. */
export async function startTracker(onFrame: (landmarks: Point[] | null) => void): Promise<Tracker> {
  const { FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision')
  const fileset = await FilesetResolver.forVisionTasks(WASM)
  const landmarker = await FaceLandmarker.createFromOptions(fileset, {
    baseOptions: { modelAssetPath: MODEL, delegate: 'GPU' },
    runningMode: 'VIDEO',
    numFaces: 1,
  })
  const stream = await navigator.mediaDevices.getUserMedia({
    video: { width: 640, height: 480, facingMode: 'user' },
    audio: false,
  })
  const video = document.createElement('video')
  video.srcObject = stream
  video.muted = true
  video.playsInline = true
  await video.play()

  let running = true
  let last = -1
  const loop = () => {
    if (!running) return
    if (video.currentTime !== last) {
      last = video.currentTime
      const result = landmarker.detectForVideo(video, performance.now())
      onFrame(result.faceLandmarks?.[0] ?? null)
    }
    requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)

  return {
    video,
    stop: () => {
      running = false
      stream.getTracks().forEach((t) => t.stop())
      landmarker.close()
    },
  }
}
