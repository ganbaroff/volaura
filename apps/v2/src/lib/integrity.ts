/*
  Camera anti-cheat v0 — current_gaps.md Gap 9.
  MediaPipe FaceLandmarker (Apache 2.0), fully client-side: the video stream
  never leaves the browser. Only aggregate counters are reported to the API
  at completion. Soft signals — never an automatic fail (Constitution: shame-free,
  honest-not-invasive).
*/

export interface IntegrityFlags {
  face_absent_seconds: number;
  max_faces_seen: number;
  gaze_away_events: number;
  tab_switches: number;
  camera_permission: "granted" | "denied" | "unavailable";
}

const WASM_CDN = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/wasm";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

const TICK_MS = 1500;
// Head-yaw proxy for "looking away": |yaw| above ~25° sustained on a tick.
const GAZE_BLENDSHAPE_THRESHOLD = 0.65;

export class IntegrityWatcher {
  private flags: IntegrityFlags = {
    face_absent_seconds: 0,
    max_faces_seen: 0,
    gaze_away_events: 0,
    tab_switches: 0,
    camera_permission: "unavailable",
  };
  private stream: MediaStream | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private landmarker: { detectForVideo: (v: HTMLVideoElement, t: number) => LandmarkerResult } | null = null;
  private video: HTMLVideoElement | null = null;
  private onVisibility = () => {
    if (document.visibilityState === "hidden") this.flags.tab_switches += 1;
  };

  /** Returns true when the camera is live and the model loaded. */
  async start(video: HTMLVideoElement): Promise<boolean> {
    document.addEventListener("visibilitychange", this.onVisibility);
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { width: 480 }, audio: false });
      this.flags.camera_permission = "granted";
    } catch {
      this.flags.camera_permission = "denied";
      return false;
    }
    video.srcObject = this.stream;
    await video.play().catch(() => undefined);
    this.video = video;
    try {
      const { FilesetResolver, FaceLandmarker } = await import("@mediapipe/tasks-vision");
      const fileset = await FilesetResolver.forVisionTasks(WASM_CDN);
      this.landmarker = await FaceLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
        runningMode: "VIDEO",
        numFaces: 2,
        outputFaceBlendshapes: true,
      });
    } catch {
      // Model failed to load (offline CDN, old device) — camera stays on as a
      // presence deterrent, counters simply stay at zero. Soft degradation.
      this.landmarker = null;
    }
    this.timer = setInterval(() => this.tick(), TICK_MS);
    return true;
  }

  private tick(): void {
    if (!this.landmarker || !this.video || this.video.readyState < 2) return;
    try {
      const result = this.landmarker.detectForVideo(this.video, performance.now());
      const faces = result.faceLandmarks?.length ?? 0;
      if (faces === 0) this.flags.face_absent_seconds += TICK_MS / 1000;
      if (faces > this.flags.max_faces_seen) this.flags.max_faces_seen = faces;
      const shapes = result.faceBlendshapes?.[0]?.categories;
      if (shapes) {
        const score = (name: string) => shapes.find((c) => c.categoryName === name)?.score ?? 0;
        const lookAway = Math.max(
          Math.min(score("eyeLookOutLeft"), score("eyeLookInRight")),
          Math.min(score("eyeLookOutRight"), score("eyeLookInLeft")),
        );
        if (lookAway > GAZE_BLENDSHAPE_THRESHOLD) this.flags.gaze_away_events += 1;
      }
    } catch {
      // Detection hiccup on one frame — never break the assessment over it.
    }
  }

  snapshot(): IntegrityFlags {
    return { ...this.flags, face_absent_seconds: Math.round(this.flags.face_absent_seconds) };
  }

  stop(): void {
    document.removeEventListener("visibilitychange", this.onVisibility);
    if (this.timer) clearInterval(this.timer);
    this.stream?.getTracks().forEach((t) => t.stop());
    this.stream = null;
    this.landmarker = null;
  }
}

interface LandmarkerResult {
  faceLandmarks?: unknown[];
  faceBlendshapes?: { categories: { categoryName: string; score: number }[] }[];
}
