import type {ProofBindingV1, ProofChallengeV1, ProofResultV1} from '../api/generated/contracts';
export type HoldBinding = ProofBindingV1 & Readonly<{route: string}>;
export type HoldProviders = Readonly<{issue: (binding: HoldBinding, signal: AbortSignal) => Promise<ProofChallengeV1>; complete: (challenge: ProofChallengeV1, binding: HoldBinding, signal: AbortSignal) => Promise<ProofResultV1>; submit: (binding: HoldBinding, proof: ProofResultV1) => Promise<unknown>; abandon?: (challenge: ProofChallengeV1) => void}>;
export function bindingEqual(a: HoldBinding, b: HoldBinding) {return (['action_code', 'target_type', 'target_id', 'base_revision', 'preview_fingerprint', 'route'] as const).every(key => a[key] === b[key]);}
export class DeliberateHold {
  phase: 'idle' | 'challenging' | 'holding' | 'completing' | 'submitted' | 'cancelled' | 'error' = 'idle';
  private sequence = 0;
  private abort: AbortController | null = null;
  private binding: HoldBinding | null = null;
  private challenge: ProofChallengeV1 | null = null;
  private started = 0;
  constructor(private providers: HoldProviders, private now: () => number = () => performance.now()) {}
  async start(binding: HoldBinding, available: boolean) {
    this.cancel(); if (!available) return;
    const sequence = ++this.sequence, abort = new AbortController(); this.abort = abort; this.binding = Object.freeze({...binding}); this.phase = 'challenging';
    try {
      const challenge = await this.providers.issue(this.binding, abort.signal);
      if (sequence !== this.sequence || abort.signal.aborted) {this.providers.abandon?.(challenge); return;}
      if (challenge.expires_in_ms !== 15000) throw new Error('Invalid challenge duration.');
      this.challenge = challenge; this.started = this.now(); this.phase = 'holding';
    } catch {if (sequence === this.sequence) this.phase = 'error';}
  }
  progress(binding: HoldBinding) {
    if (this.phase !== 'holding' || !this.binding || !bindingEqual(binding, this.binding) || this.now() - this.started >= 15000) {if (this.phase === 'holding') this.cancel(); return 0;}
    return Math.min(1, Math.max(0, (this.now() - this.started) / 3000));
  }
  async finish(binding: HoldBinding): Promise<unknown | null> {
    if (this.progress(binding) < 1 || this.phase !== 'holding' || !this.challenge || !this.binding || !this.abort) return null;
    const sequence = this.sequence, captured = this.binding, abort = this.abort; this.phase = 'completing';
    try {
      const proof = await this.providers.complete(this.challenge, captured, abort.signal);
      if (sequence !== this.sequence || abort.signal.aborted || !bindingEqual(binding, captured)) return null;
      this.phase = 'submitted'; // claim the dispatch before awaiting the owner
      return await this.providers.submit(captured, proof);
    } catch {if (sequence === this.sequence) this.phase = 'error'; return null;}
  }
  cancel() {++this.sequence; this.abort?.abort(); if (this.challenge && this.phase !== 'submitted') this.providers.abandon?.(this.challenge); this.abort = null; this.challenge = null; this.binding = null; this.phase = 'cancelled';}
}
