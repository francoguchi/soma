import {useEffect, useRef, useState} from 'react';
import {bindingEqual, DeliberateHold, type HoldBinding, type HoldProviders} from '../interactions/hold';
export function HoldButton({label, binding, available, providers}: {label: string; binding: HoldBinding; available: boolean; providers: HoldProviders}) {
  const hold = useRef(new DeliberateHold(providers));
  const previousProviders = useRef(providers);
  const current = useRef(binding), pressed = useRef(false), pointer = useRef<{x: number; y: number} | null>(null);
  const [progress, setProgress] = useState(0), [status, setStatus] = useState('Hold continuously for 3 seconds.');
  const cancel = () => {pressed.current = false; pointer.current = null; if (hold.current.phase === 'submitted') return; hold.current.cancel(); setProgress(0); setStatus('Hold cancelled.');};
  useEffect(() => {if (!bindingEqual(current.current, binding) || !available) cancel(); current.current = binding;}, [binding, available]);
  useEffect(() => {if (previousProviders.current !== providers) {cancel(); hold.current = new DeliberateHold(providers); previousProviders.current = providers;}}, [providers]);
  useEffect(() => {
    const visibility = () => {if (document.hidden) cancel();};
    addEventListener('blur', cancel); addEventListener('soma-scroll-gesture', cancel); addEventListener('popstate', cancel); document.addEventListener('scroll', cancel, true); document.addEventListener('visibilitychange', visibility);
    return () => {pressed.current = false; hold.current.cancel(); removeEventListener('blur', cancel); removeEventListener('soma-scroll-gesture', cancel); removeEventListener('popstate', cancel); document.removeEventListener('scroll', cancel, true); document.removeEventListener('visibilitychange', visibility);};
  }, []);
  const start = async () => {
    if (pressed.current || !available || hold.current.phase === 'submitted') return;
    pressed.current = true; setStatus('Preparing confirmation…'); await hold.current.start(current.current, available);
    if (!pressed.current) return;
    const frame = () => {
      if (!pressed.current) return;
      const value = hold.current.progress(current.current); setProgress(value);
      if (hold.current.phase !== 'holding') {cancel(); return;}
      setStatus('Keep holding. Release to cancel.');
      if (value === 1) {setStatus('Checking with the action owner…'); void hold.current.finish(current.current).then(result => {pressed.current = false; setStatus(result === null ? 'Action did not complete. Refresh its eligibility.' : 'Action owner accepted the command.');});}
      else requestAnimationFrame(frame);
    };
    if (hold.current.phase === 'holding') requestAnimationFrame(frame); else cancel();
  };
  return <div className="deliberate-hold"><button type="button" disabled={!available} onPointerDown={event => {if (event.button === 0) {pointer.current = {x: event.clientX, y: event.clientY}; event.currentTarget.setPointerCapture(event.pointerId); void start();}}} onPointerMove={event => {if (pointer.current && Math.hypot(event.clientX - pointer.current.x, event.clientY - pointer.current.y) >= 8) cancel();}} onPointerUp={cancel} onPointerCancel={cancel} onLostPointerCapture={() => {if (pressed.current) cancel();}} onBlur={() => {if (pressed.current) cancel();}} onKeyDown={event => {if (event.key === 'Escape') {event.preventDefault(); cancel();} if (event.key === ' ' || event.key === 'Enter') {event.preventDefault(); if (!event.repeat) void start();}}} onKeyUp={event => {if (event.key === ' ' || event.key === 'Enter') {event.preventDefault(); cancel();}}}>{label}</button><progress max={1} value={progress} aria-label="Deliberate hold progress"/><p role="status">{status}</p></div>;
}
