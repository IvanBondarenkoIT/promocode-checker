let audioCtx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") {
    return null;
  }
  const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctx) {
    return null;
  }
  if (!audioCtx) {
    audioCtx = new Ctx();
  }
  return audioCtx;
}

function tone(frequency: number, durationMs: number, startAt: number): void {
  const ctx = getCtx();
  if (!ctx) {
    return;
  }
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.type = "square";
  oscillator.frequency.value = frequency;
  gain.gain.value = 0.08;
  oscillator.connect(gain);
  gain.connect(ctx.destination);
  oscillator.start(startAt);
  oscillator.stop(startAt + durationMs / 1000);
}

/** ACTIVE / success: one short high beep */
export function playSuccessBeep(): void {
  const ctx = getCtx();
  if (!ctx) {
    return;
  }
  void ctx.resume();
  tone(880, 120, ctx.currentTime);
}

/** USED / NOT_FOUND / errors: two low buzzes */
export function playErrorBuzz(): void {
  const ctx = getCtx();
  if (!ctx) {
    return;
  }
  void ctx.resume();
  const now = ctx.currentTime;
  tone(220, 140, now);
  tone(180, 160, now + 0.2);
}
