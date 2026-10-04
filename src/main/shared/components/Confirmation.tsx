import {useEffect, useMemo, useRef, useState, type ReactNode, type RefObject} from 'react';
import {bindingEqual, type HoldBinding, type HoldProviders} from '../interactions/hold';
import {HoldButton} from './HoldButton';
import {Modal} from './Modal';
import {ErrorState} from './ErrorState';
export type ConfirmationTier = 'ordinary' | 'hold' | 'preview' | 'preview_plus_hold' | 'domain_authority';
export type ImpactPreview = Readonly<{binding: HoldBinding; targets: readonly string[]; effects: readonly string[]; blockers: readonly string[]; current: boolean}>;
/** The owner supplies eligibility, preview and its atomic command. Shared UI supplies friction only. */
export function Confirmation({tier, label, binding, available, preview, providers, activate, authority, application, fallback}: {
  tier: ConfirmationTier; label: string; binding: HoldBinding; available: boolean; preview?: ImpactPreview; providers?: HoldProviders;
  activate: () => Promise<unknown>; authority?: ReactNode; application: RefObject<HTMLElement | null>; fallback: () => HTMLElement | null;
}) {
  const [open, setOpen] = useState(false), [pending, setPending] = useState(false), [error, setError] = useState<unknown>(null);
  const active = useRef(false), prior = useRef(binding);
  const guardedProviders = useMemo(() => providers ? {...providers, submit: async (captured: HoldBinding, proof: Parameters<HoldProviders['submit']>[1]) => {
    if (active.current) return null;
    active.current = true; setPending(true); setError(null);
    try {const result = await providers.submit(captured, proof); setOpen(false); return result;}
    catch (caught) {setError(caught); throw caught;}
    finally {active.current = false; setPending(false);}
  }} : undefined, [providers]);
  useEffect(() => {if (!bindingEqual(prior.current, binding) || !available) setOpen(false); prior.current = binding;}, [binding, available]);
  const needsPreview = tier === 'preview' || tier === 'preview_plus_hold';
  const needsHold = tier === 'hold' || tier === 'preview_plus_hold';
  const eligible = available && (!needsPreview || !!preview && preview.current && bindingEqual(preview.binding, binding) && preview.blockers.length === 0 && /^[0-9a-f]{64}$/u.test(binding.preview_fingerprint ?? ''));
  const dispatch = async () => {if (!eligible || active.current) return; active.current = true; setPending(true); setError(null); try {await activate(); setOpen(false);} catch (caught) {setError(caught);} finally {active.current = false; setPending(false);}};
  const consequence = (isolated: boolean) => needsHold ? guardedProviders ? <HoldButton label={label} binding={binding} available={isolated && eligible} providers={guardedProviders}/> : <p>Confirmation provider unavailable.</p> : tier === 'domain_authority' ? authority ?? <p>Owner authority unavailable.</p> : <button disabled={!isolated || !eligible || pending} onClick={() => {void dispatch();}}>{pending ? 'Waiting for action owner…' : label}</button>;
  return <div className="confirmation">{tier === 'ordinary' ? <button disabled={!eligible || pending} onClick={() => {void dispatch();}}>{label}</button> : tier === 'hold' ? consequence(true) : <button disabled={!available} onClick={() => setOpen(true)}>{label}…</button>}
    {error !== null && <ErrorState error={error}/>}{open && <Modal title={label} application={application} fallback={fallback} close={() => setOpen(false)} dismissible={!pending}>{isolated => <>
      {needsPreview && (preview ? <div className="impact-preview"><h3>Material targets</h3><ul>{preview.targets.map((item, i) => <li key={i}>{item}</li>)}</ul><h3>Effects</h3><ul>{preview.effects.map((item, i) => <li key={i}>{item}</li>)}</ul>{preview.blockers.length > 0 && <><h3>Blocked</h3><ul>{preview.blockers.map((item, i) => <li key={i}>{item}</li>)}</ul></>}{!eligible && <p role="alert">The owner preview is stale, blocked or unavailable. Refresh before continuing.</p>}</div> : <p role="alert">Owner preview unavailable.</p>)}
      {consequence(isolated)}{error !== null && <ErrorState error={error}/>}</>}</Modal>}</div>;
}
