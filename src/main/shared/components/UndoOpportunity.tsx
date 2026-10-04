import {useEffect, useState} from 'react';
import {SafeUndo, type InversePreview} from '../interactions/undo';
export function UndoOpportunity({undo, id}: {undo: SafeUndo; id: string}) {
  const [preview, setPreview] = useState<InversePreview>({state: 'INDETERMINATE', fingerprint: null, reason: 'Checking the owner inverse.', consequence: null, blockers: []}), [pending, setPending] = useState(false), [done, setDone] = useState(false);
  useEffect(() => {let alive = true; void undo.availability(id).then(value => {if (alive) setPreview(value);}); return () => {alive = false;};}, [undo, id]);
  if (done) return <p role="status">The owning correction command completed.</p>;
  return <div>{preview.consequence && <p>{preview.consequence}</p>}<button disabled={pending || preview.state !== 'AVAILABLE'} onClick={() => {setPending(true); void undo.execute(id, preview.fingerprint ?? undefined).then(success => {if (success) setDone(true); else setPreview({state: 'STALE', fingerprint: null, reason: 'The inverse changed or became unavailable. Refresh the owning correction workflow.', consequence: null, blockers: []});}).finally(() => setPending(false));}}>Undo this action</button>{preview.reason && <p role="status">{preview.reason}</p>}{preview.blockers.length > 0 && <ul>{preview.blockers.map((blocker,i)=><li key={i}>{blocker}</li>)}</ul>}</div>;
}
