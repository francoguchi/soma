import {SectionHeading, Action} from '../../../shared/components/Section';
import {useEffect, useState, type RefObject} from 'react';
import type * as C from '../../../shared/api/generated/contracts';
import {referenceApi as commands} from '../api';
import {Confirmation} from '../../../shared/components/Confirmation';
import {dialogFallback} from '../../../shared/components/Modal';
import {useWorkingIntent} from '../../../shared/interactions/use-working-intent';
import {CustomerChooser, Field, QueryState, identityPage, useOwnerAction, useOwnerQuery} from '../model';

export function AccountCode({detail, application, refresh, showClaimants}: {detail: C.ReferenceCustomerDetailV1; application: RefObject<HTMLElement | null>; refresh: () => void; showClaimants: (code: string) => void}) {
  const id = detail.reference_id;
  const working = useWorkingIntent({code: detail.current_account_code?.value_text ?? '', mode: 'CONFIRM_SHARED_CLAIM', source: '', reason: ''}, {contract_id: 'reference.edit.customer_organization.account_code', contract_version: 1, target_type: 'customer_organization', target_id: id, scope_key: 'account_code', base_revision: String(detail.revision)}, application);
  const {code, source, reason} = working.draft;
  const mode = working.draft.mode === 'REASSIGN_CLAIM' ? 'REASSIGN_CLAIM' : 'CONFIRM_SHARED_CLAIM';
  const setCode = (v: string) => working.edit('code', v), setMode = (v: string) => working.edit('mode', v), setSource = (v: string) => working.edit('source', v), setReason = (v: string) => working.edit('reason', v);
  const [review, setReview] = useState<C.ReferenceReviewResultV1 | null>(null), [reviewError, setReviewError] = useState<unknown>(null), [loading, setLoading] = useState(false);
  const action = useOwnerAction();
  useEffect(() => {setReview(null);}, [code, mode, source, detail.revision]);
  const sourceName = useOwnerQuery(source, signal => source ? identityPage('customer_organization', [source], signal) : Promise.resolve({items: []}));
  async function preview() {
    setReview(null); setLoading(true); setReviewError(null);
    try {setReview(await commands.reviewAccountCode({raw_account_code: code, proposed_action: mode, target_customer_org_id: id, ...(mode === 'REASSIGN_CLAIM' ? {from_customer_org_id: source} : {})}));}
    catch (error) {setReviewError(error);} finally {setLoading(false);}
  }
  const binding = {action_code: 'reference.account-code.review', target_type: 'customer_organization', target_id: id, base_revision: String(review?.target_revision ?? detail.revision), preview_fingerprint: review?.review_snapshot_hash ?? null, route: '/settings/reference-data/customer_organization/' + id};
  const submit = async () => {
    if (!review) return;
    const captured = review;
    const success = await action.run(JSON.stringify({id, mode, source, code, reason, review: captured}), command => mode === 'CONFIRM_SHARED_CLAIM' ? commands.shareAccountCode({id}, {command_id: command, base_revision: captured.target_revision, account_code: code, review_snapshot_hash: captured.review_snapshot_hash, reason_category: reason}) : commands.reassignAccountCode({command_id: command, from_customer_org_id: source, from_base_revision: captured.source_revision!, to_customer_org_id: id, to_base_revision: captured.target_revision, account_code: code, review_snapshot_hash: captured.review_snapshot_hash, reason_category: reason}), async () => {await working.accepted(); setReview(null); refresh();});
    if (!success) setReview(null);
  };
  return <section><SectionHeading level={3} icon="reference">Account Code</SectionHeading><p>Current: {detail.current_account_code?.value_text ?? 'None'}. Shared claims remain ambiguous external evidence.</p><div className="operational-form"><Field label="Account Code" value={code} change={setCode} maximum={512} disabled={detail.lifecycle_state !== 'active' || action.busy || action.pending}/><Action disabled={!code || detail.lifecycle_state !== 'active' || action.busy || working.conflict} onClick={() => {void action.run(JSON.stringify({id, code, rev: detail.revision}), command => commands.setAccountCode({id}, {command_id: command, base_revision: detail.revision, account_code: code}), async () => {await working.accepted(undefined, ['code']); refresh();});}}>Set Account Code</Action>
    <label>Reviewed action<select disabled={action.busy || action.pending} value={mode} onChange={e => setMode(e.target.value as typeof mode)}><option value="CONFIRM_SHARED_CLAIM">Confirm shared claim</option><option value="REASSIGN_CLAIM">Reassign one source claim</option></select></label>
    {mode === 'REASSIGN_CLAIM' && <CustomerChooser label="Source Customer" value={source} change={setSource} allowUnbound={false} disabled={action.busy || action.pending}/>}
    <Field label="Account Code reason category" value={reason} change={setReason} maximum={128} disabled={action.busy || action.pending}/>
    <Action disabled={loading || !code || detail.lifecycle_state !== 'active' || mode === 'REASSIGN_CLAIM' && (!source || source === id)} onClick={() => {void preview();}}>Load Account Code review</Action>
    <QueryState query={{error: reviewError, loading, reload: () => {void preview();}}}/>
    {review && <><p>Proposed action: {mode === 'REASSIGN_CLAIM' ? 'Reassign one claim' : 'Confirm shared claim'}.</p><p>Target: {detail.name} · revision {review.target_revision}. {mode === 'REASSIGN_CLAIM' && <>Source: {sourceName.value?.items[0]?.name ?? 'Selected Customer'} · revision {review.source_revision}.</>}</p><p>Exact claimant count: {review.claimant_count}</p><details><summary>Review fingerprint</summary><code>{review.review_snapshot_hash}</code></details><Action icon="search" onClick={() => showClaimants(code)}>Show claimants in collection</Action>
    <Confirmation tier="domain_authority" label="Confirm reviewed Account Code action" binding={binding} available={!action.busy && !working.conflict && !!reason && review.target_revision === detail.revision} activate={submit} application={application} fallback={() => dialogFallback(application)} authority={<><p>{mode === 'REASSIGN_CLAIM' ? 'Move only the selected source claim; unrelated claimants survive.' : 'Add an explicitly reviewed shared claim; matching remains ambiguous.'}</p><p>{detail.name} · revision {review.target_revision} · {review.claimant_count} claimants</p><Action disabled={action.busy} onClick={() => {void submit();}}>Submit exact reviewed action</Action>{action.feedback}</>}/></>}
    </div>{working.recovery}{action.feedback}{action.error !== null && <p>On stale review, load and review again. The old fingerprint is never replaced automatically.</p>}</section>;
}
