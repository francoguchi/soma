import type {ApiClient} from './client';
import type {ProofBindingV1, ProofChallengeV1, ProofResultV1, WorkingCopyKeyV1, WorkingCopyRestoreV1, WorkingCopyResultV1} from './generated/contracts';
import type {HoldBinding, HoldProviders} from '../interactions/hold';
import type {RecoveryTransport} from '../interactions/working-copy';
/** Reject values which JSON.stringify would silently change or omit. */
export function draftJson(value: unknown): string {
  const seen = new Set<object>();
  const visit = (item: unknown, depth: number): void => {
    if (depth > 32) throw new Error('Recovery draft is too deeply nested.');
    if (item === null || typeof item === 'boolean') return;
    if (typeof item === 'string') {if (/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(item)) throw new Error('Invalid draft text.'); return;}
    if (typeof item === 'number') {if (!Number.isFinite(item)) throw new Error('Invalid draft number.'); return;}
    if (typeof item !== 'object' || seen.has(item)) throw new Error('Recovery requires finite JSON values.');
    seen.add(item);
    if (Array.isArray(item)) {for (let i = 0; i < item.length; i++) {if (!(i in item)) throw new Error('Sparse draft array.'); visit(item[i], depth + 1);}}
    else {if (Object.getPrototypeOf(item) !== Object.prototype && Object.getPrototypeOf(item) !== null || Object.getOwnPropertySymbols(item).length) throw new Error('Recovery requires a plain JSON object.'); for (const key of Object.keys(item)) {visit(key, depth + 1); const descriptor = Object.getOwnPropertyDescriptor(item, key)!; if (!('value' in descriptor)) throw new Error('Draft accessors are not JSON.'); visit(descriptor.value, depth + 1);}}
    seen.delete(item);
  };
  visit(value, 0); const json = JSON.stringify(value);
  if (new TextEncoder().encode(json).length > 262144) throw new Error('Recovery draft exceeds its byte limit.');
  return json;
}
export type RecoveryIntent<T> = Readonly<{draft: T; dirty_paths: readonly string[]}>;
export function recoveryTransport<T>(client: ApiClient, key: WorkingCopyKeyV1): RecoveryTransport<RecoveryIntent<T>> {
  const binding = Object.freeze({...key});
  return async (intent, generation, commandId, signal) => {
    const result = await client.request<WorkingCopyResultV1>('/api/v1/working-copies/checkpoint', 'working-copy-result', {method: 'POST', requestContract: 'working-copy-checkpoint-request', signal,
      body: {...binding, command_id: commandId, expected_generation: generation, draft_json: draftJson(intent.draft), dirty_paths: intent.dirty_paths}});
    if (result.outcome === 'DISCARDED') throw new Error('Unexpected recovery result.');
    return {workingCopyId: result.working_copy_id, generation: result.generation, contentHash: result.draft_sha256};
  };
}
export function restoreRecovery(client: ApiClient, key: WorkingCopyKeyV1, signal?: AbortSignal): Promise<WorkingCopyRestoreV1> {
  return client.request('/api/v1/working-copies/restore', 'working-copy-restore', {method: 'POST', requestContract: 'working-copy-key', body: key, ...(signal ? {signal} : {})});
}
export function discardRecovery(client: ApiClient, id: string, generation: number, commandId: string): Promise<WorkingCopyResultV1> {
  return client.request('/api/v1/working-copies/discard', 'working-copy-result', {method: 'POST', requestContract: 'working-copy-discard-request', body: {working_copy_id: id, expected_generation: generation, command_id: commandId}});
}
export function proofBinding(binding: HoldBinding): ProofBindingV1 {const {route: _, ...wire} = binding; return wire;}
export function holdProviders(client: ApiClient, submit: HoldProviders['submit']): HoldProviders {
  return Object.freeze({
    issue: (binding: HoldBinding, signal: AbortSignal) => client.request<ProofChallengeV1>('/api/v1/confirmation/challenge', 'proof-challenge', {method: 'POST', requestContract: 'proof-binding', body: proofBinding(binding), signal}),
    complete: (challenge: ProofChallengeV1, binding: HoldBinding, signal: AbortSignal) => client.request<ProofResultV1>('/api/v1/confirmation/complete', 'proof-result', {method: 'POST', requestContract: 'proof-completion-request', body: {challenge_id: challenge.challenge_id, binding: proofBinding(binding)}, signal}),
    abandon: (challenge: ProofChallengeV1) => {void client.request('/api/v1/confirmation/abandon', 'empty-request', {method: 'POST', requestContract: 'proof-abandon-request', body: {challenge_id: challenge.challenge_id}}).catch(() => {});}, submit,
  });
}
