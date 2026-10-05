import {createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode, type RefObject} from 'react';
import {api, ApiError} from '../api/client';
import type {WorkingCopyKeyV1, WorkingCopyRestoreV1} from '../api/generated/contracts';
import {discardRecovery, recoveryTransport, restoreRecovery, type RecoveryIntent} from '../api/recovery';
import {WorkingCopyClient} from './working-copy';
import {NavigationGuard, warnBeforeUnload} from './navigation-guard';
import {Modal, dialogFallback} from '../components/Modal';

const WorkingSurfaceContext = createContext(true);
export function WorkingSurface({active, children}: {active: boolean; children: ReactNode}) {return <WorkingSurfaceContext.Provider value={active}>{children}</WorkingSurfaceContext.Provider>;}

export function requestNavigation(flow: string, proceed: () => void) {
  const event = new CustomEvent('soma:navigate', {cancelable: true, detail: {flow, proceed}});
  if (dispatchEvent(event)) proceed();
}

/** Owner forms retain failed intent and use Foundation's checkpoint/guard mechanics. */
export function useWorkingIntent<T extends Record<string, string>>(initial: T, key: WorkingCopyKeyV1, application: RefObject<HTMLElement | null>) {
  const active = useContext(WorkingSurfaceContext), activeRef = useRef(active); activeRef.current = active;
  const [draft, setDraft] = useState(initial), [version, update] = useState(0);
  const draftRef = useRef(draft); draftRef.current = draft;
  const baseline = useRef(initial);
  const [recovered, setRecovered] = useState<WorkingCopyRestoreV1 | null>(null);
  const [recoveryError, setRecoveryError] = useState<unknown>(null), [leaving, setLeaving] = useState(false);
  const [needsReview, setNeedsReview] = useState(false);
  const keyString = JSON.stringify(key);
  const client = useMemo(() => new WorkingCopyClient<RecoveryIntent<T>>(recoveryTransport(api, key), () => update(v => v + 1)), [keyString]);
  const guard = useRef(new NavigationGuard());
  const dirtyPaths = Object.keys(draft).filter(name => draft[name] !== baseline.current[name]).sort().map(name => '/' + name);
  const dirty = dirtyPaths.length > 0;
  const status = client.status;
  const current = useRef({dirty, recovered}); current.current = {dirty, recovered};
  const priorKey = useRef(keyString);
  useEffect(() => {
    if (priorKey.current !== keyString) {
      if (current.current.dirty) setNeedsReview(true);
      else {baseline.current = initial; draftRef.current = initial; setDraft(initial);}
    }
    priorKey.current = keyString;
    const abort = new AbortController();
    void restoreRecovery(api, key, abort.signal).then(value => {if (!abort.signal.aborted) setRecovered(value);}).catch(error => {
      if (!abort.signal.aborted && !(error instanceof ApiError && error.detail.code === 'WORKING_COPY_NOT_FOUND')) setRecoveryError(error);
    });
    const before = warnBeforeUnload(() => activeRef.current && current.current.dirty);
    const navigation = (raw: Event) => {
      const event = raw as CustomEvent<{flow: string; proceed: () => void}>;
      if (!activeRef.current || !current.current.dirty || event.defaultPrevented) return;
      event.preventDefault();
      if (!guard.current.request(keyString, event.detail.flow, true, event.detail.proceed)) setLeaving(true);
    };
    addEventListener('soma:navigate', navigation);
    return () => {abort.abort(); before(); removeEventListener('soma:navigate', navigation); client.dispose();};
  }, [keyString, client]);
  const edit = (name: keyof T, value: string) => {
    const next = {...draftRef.current, [name]: value}; draftRef.current = next; setDraft(next);
    const paths = Object.keys(next).filter(field => next[field] !== baseline.current[field]).sort().map(field => '/' + field);
    if (paths.length) client.edit({draft: next, dirty_paths: paths}); else client.acceptedSave();
  };
  const clearCheckpoint = async () => {
    const checkpoint = client.checkpointIdentity() ?? (recovered ? {id: recovered.working_copy_id, generation: recovered.generation} : null);
    if (checkpoint) await discardRecovery(api, checkpoint.id, checkpoint.generation, crypto.randomUUID());
    setRecovered(null);
  };
  const accepted = async (reset?: T, fields?: readonly (keyof T)[]) => {
    try {await clearCheckpoint();} catch (error) {setRecoveryError(error);}
    if (keyString !== priorKey.current) {setNeedsReview(true); return;}
    baseline.current = reset ?? (fields ? {...baseline.current, ...Object.fromEntries(fields.map(field => [field, draftRef.current[field]]))} : draftRef.current);
    if (reset) {draftRef.current = reset; setDraft(reset);}
    const paths = Object.keys(draftRef.current).filter(field => draftRef.current[field] !== baseline.current[field]).sort().map(field => '/' + field);
    current.current.dirty = paths.length > 0; setNeedsReview(false); client.acceptedSave();
    if (paths.length) client.edit({draft: draftRef.current, dirty_paths: paths});
  };
  const restore = async () => {
    if (!recovered || dirty) return;
    try {
      const value = JSON.parse(recovered.draft_json) as T;
      if (Object.keys(value).sort().join() !== Object.keys(initial).sort().join() || Object.values(value).some(v => typeof v !== 'string')) throw new Error('Recovered fields do not match this owner form.');
      client.restore({draft: value, dirty_paths: recovered.dirty_paths}, {workingCopyId: recovered.working_copy_id, generation: recovered.generation, contentHash: recovered.draft_sha256}, recovered.conflict ? 'STALE' : 'CURRENT'); setDraft(value);
    } catch (error) {setRecoveryError(error);}
  };
  const reviewCurrent = async () => {
    try {await clearCheckpoint(); baseline.current = initial; client.acceptedSave(); const paths = Object.keys(draft).filter(field => draft[field] !== initial[field]).sort().map(field => '/' + field); if (paths.length) client.edit({draft, dirty_paths: paths}); setNeedsReview(false);} catch (error) {setRecoveryError(error);}
  };
  const discard = async () => {
    try {await clearCheckpoint(); baseline.current = initial; draftRef.current = initial; setDraft(initial); current.current.dirty = false; client.acceptedSave(); setNeedsReview(false);} catch (error) {setRecoveryError(error);}
  };
  void version;
  const recovery = <>
    {dirty && <><p role="status">Unsaved {key.scope_key.replaceAll('_', ' ')} fields: {dirtyPaths.map(p => p.slice(1).replaceAll('_', ' ')).join(', ')}. Recovery: {status.replaceAll('_', ' ')}.</p><button type="button" onClick={() => {void discard();}}>Discard {key.scope_key.replaceAll('_', ' ')} intent</button></>}
    {recovered && !dirty && <div><p>Recoverable intent is available{recovered.conflict ? ' from an older revision' : ''}.</p><button type="button" onClick={() => {void restore();}}>Restore intent</button><button type="button" onClick={() => {void clearCheckpoint().catch(setRecoveryError);}}>Discard recovered intent</button></div>}
    {(status === 'conflict' || needsReview) && <><p role="alert">Working intent is stale. Review every field against the current record before saving.</p><button type="button" onClick={() => {void reviewCurrent();}}>Use reviewed intent against current revision</button></>}
    {recoveryError !== null && <p role="alert">Recovery is unavailable. Your in-memory input is retained.</p>}
    {leaving && <Modal title="Leave unsaved changes?" application={application} fallback={() => dialogFallback(application)} close={() => {guard.current.stay(); setLeaving(false);}}>{isolated => <><p>Unsaved intent has not been accepted. Stay to save or review recovery status before leaving.</p><button disabled={!isolated} onClick={() => {setLeaving(false); guard.current.abandon();}}>Leave without saving</button></>}</Modal>}
  </>;
  return {draft, edit, dirty, accepted, discard, recovery, conflict: status === 'conflict' || needsReview};
}
