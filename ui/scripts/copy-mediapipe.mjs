// Copies MediaPipe's WASM runtime from node_modules into public/, so the eye-tracking page loads
// everything from our own site (no third-party CDN). Runs before `dev` and `build`.
import { cpSync, mkdirSync } from 'node:fs'

const from = 'node_modules/@mediapipe/tasks-vision/wasm'
const to = 'public/mediapipe/wasm'
mkdirSync(to, { recursive: true })
for (const f of ['vision_wasm_internal.js', 'vision_wasm_internal.wasm']) cpSync(`${from}/${f}`, `${to}/${f}`)
