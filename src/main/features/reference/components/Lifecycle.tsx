import {useEffect, useState, type RefObject} from 'react';
import type * as C from '../../../shared/api/generated/contracts';
import {Confirmation} from '../../../shared/components/Confirmation';
import {dialogFallback} from '../../../shared/components/Modal';
import {useWorkingIntent} from '../../../shared/interactions/use-working-intent';
import {referenceApi as commands} from '../api';
import {Field, QueryState, useOwnerAction, type Detail, type Kind} from '../model';

export function Lifecycle({kind, detail, application, refresh}: {kind: Kind; detail: Detail; application: RefObject<HTMLElement | null>; refresh: () => void}) {
  const [preview, setPreview] = useState<C.ReferenceBlockerPreviewV1 | null>(null), [error, setError] = useState<unknown>(null), [loading, setLoading] = useState(false);
  const action = useOwnerAction(), id = detail.reference_id;
  const working = useWorkingIntent({reason: ''}, {contract_id: 'reference.edit.' + kind + '.lifecycle', contract_version: 1, target_type: kind, target_id: id, scope_key: 'lifecycle', base_revision: String(detail.revision)}, application);
  const reason = working.draft.reason, setReason = (v: string) => working.edit('reason', v);
  useEffect(() => {setPreview(null);}, [id, detail.revision]);
  const load = async (after?: string) => {
    setLoading(true); setError(null);
    try {setPreview(await commands.archivePreview({reference_type: kind, id}, {base_revision: detail.revision, limit: 50, ...(after ? {after} : {})}));} catch (caught) {setError(caught); setPreview(null);} finally {setLoading(false);}
  };
  const binding = {action_code: 'reference.' + (detail.lifecycle_state === 'active' ? 'archive' : 'reactivate'), target_type: kind, target_id: id, base_revision: String(detail.revision), preview_fingerprint: null, route: '/settings/reference-data/' + kind + '/' + id};
  const submit = () => action.run(JSON.stringify({kind, id, revision: detail.revision, reason, state: detail.lifecycle_state}), command => detail.lifecycle_state === 'active' ? commands.archive({reference_type: kind, id}, {command_id: command, base_revision: detail.revision, reason_category: reason}) : commands.reactivate({reference_type: kind, id}, {command_id: command, base_revision: detail.revision, reason_category: reason}), async () => {await working.accepted(); setPreview(null); refresh();});
  const eligible = detail.lifecycle_state === 'archived' || !!preview && preview.would_be_eligible && preview.exact_blocker_count === 0 && preview.revision === detail.revision;
  return <section><h3>Lifecycle</h3><p>{detail.lifecycle_state} · revision {detail.revision}</p><Field label="Lifecycle reason category" value={reason} change={setReason} maximum={128} disabled={action.busy || action.pending}/>{detail.lifecycle_state === 'active' && <button disabled={loading || action.busy} onClick={() => {void load();}}>Preview archive dependencies</button>}<QueryState query={{error, loading, reload: () => {void load();}}}/>
  {preview && <><p role="status">Exact blocker count: {preview.exact_blocker_count} · {preview.would_be_eligible ? 'Preview eligible' : 'Blocked or indeterminate'}</p><ul className="evidence-list">{preview.blockers.map(row => <li key={row.validator_id + row.blocker_id}>{row.validator_id} · {row.reason_code}<p>Review the owning dependency before retrying.</p><details><summary>Dependency identity</summary>{row.blocker_id}</details></li>)}</ul>{preview.continuation && <button onClick={() => {void load(preview.continuation!);}}>Next blocker page</button>}<p>The command revalidates dependencies transactionally. A preview does not guarantee acceptance.</p></>}
  <Confirmation tier="domain_authority" label={detail.lifecycle_state === 'active' ? 'Archive reference' : 'Reactivate reference'} binding={binding} available={eligible && !!reason && !action.busy && !working.conflict} application={application} fallback={() => dialogFallback(application)} activate={submit} authority={<><p>{detail.lifecycle_state === 'active' ? 'Archive' : 'Reactivate'} {detail.name}, revision {detail.revision}.</p><button disabled={!eligible || action.busy} onClick={() => {void submit();}}>Confirm lifecycle operation</button>{action.feedback}</>}/>{action.feedback}
  {working.recovery}</section>;
}
