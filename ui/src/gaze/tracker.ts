// Webcam face tracking with MediaPipe Face Landmarker (Apache-2.0), entirely in the browser.
// The video never leaves the page: only landmark coordinates are used, and nothing is sent to
// a server. The library and model are loaded from this site only when the gaze page opens.
import type { Point } from './model'

// Served from our own site: the WASM is copied from the npm package at build time
// (scripts/copy-mediapipe.mjs), the model is in public/mediapipe (see NOTICE.md there).
const WASM = `${import.meta.env.BASE_URL}mediapipe/wasm`
const MODEL = `${import.meta.env.BASE_URL}mediapipe/face_landmarker.task`

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
