import {useState} from 'react';
import type * as C from '../../../shared/api/generated/contracts';
import {api} from '../../../shared/api/client';
import type {Page} from '../../../shared/collections/BoundedCollection';
import {Action, FormActions} from '../../../shared/components/Section';
import {CustomerChooser, Field, identityPage, type Kind, type Identity} from '../model';

export type MatchRequest = Readonly<Record<string, string>>;
export type ReferenceCollectionPage = Page<Identity> & {evidence?: C.ReferenceCandidateResultV1; criteria?: MatchRequest};
const explanations: Record<string, string> = {
  ACCOUNT_CODE_MULTIPLE_CLAIMS: 'Multiple Customers claim this Account Code.',
  ACCOUNT_CODE_NAME_CONFLICT: 'The Account Code and name identify different Customers.',
  ACCOUNT_CODE_MATCH: 'Matched by Account Code.',
  ACCOUNT_CODE_UNRESOLVED_NAME_CANDIDATE: 'No Account Code match; one Customer matches the name.',
  ACCOUNT_CODE_UNRESOLVED_NAME_AMBIGUOUS: 'No Account Code match; multiple Customers match the name.',
  NAME_EMAIL_MATCH: 'Matched by name or email within the selected affiliation.',
  NAME_MATCH: 'Matched by name.',
};
export async function candidatePage(kind: Kind, request: MatchRequest, after: string | null, limit: number, signal: AbortSignal): Promise<ReferenceCollectionPage> {
  const suffix = kind === 'customer_organization' ? 'customer-organization' : 'contact';
  const evidence = await api.request<C.ReferenceCandidateResultV1>('/api/v1/reference/match/' + suffix, 'urn:soma:01:candidate-result:v1', {
    method: 'POST', body: {...request, limit, ...(after ? {after} : {})},
    requestContract: 'urn:soma:01:match-' + (kind === 'contact' ? 'contact' : 'customer') + '-request:v1', signal,
  });
  const details = await identityPage(kind, evidence.candidate_ids, signal);
  return {evidence, criteria: request, items: details.items, continuation: evidence.continuation, total: evidence.candidate_count, as_of_utc_s: 0, warnings: [], partial: false};
}
export function CandidateSummary({evidence, countOnPage}: {evidence: C.ReferenceCandidateResultV1; countOnPage: number}) {
  const state = evidence.state === 'AMBIGUOUS' ? 'Ambiguous' : evidence.state === 'UNIQUE_CANDIDATE' ? 'Unique candidate' : 'No exact candidates';
  return <div className="collection-summary" data-candidate-state={evidence.state}>
    <p role="status">{state}{evidence.candidate_count > 0 && <> · {evidence.candidate_count} exact {evidence.candidate_count === 1 ? 'candidate' : 'candidates'}{evidence.continuation || countOnPage < evidence.candidate_count ? ` · ${countOnPage} on this page` : ''}</>}</p>
    {evidence.candidate_count > 0 && <p>{explanations[evidence.explanation] ?? 'Matched by exact evidence.'} Opening does not accept a link or merge.</p>}
    {evidence.candidate_count === 0 && <p>Try other evidence or clear search.</p>}
  </div>;
}
/** Expert fields supply owner query intent; results belong only to the primary collection. */
export function AdvancedMatching({kind, disabled, submit}: {kind: Kind; disabled: boolean; submit: (request: MatchRequest) => void}) {
  const [name, setName] = useState(''), [secondary, setSecondary] = useState(''), [scope, setScope] = useState('');
  if (kind === 'dispatch_location') return null;
  return <form className="operational-form" onSubmit={event => {
    event.preventDefault(); if (disabled) return;
    submit(kind === 'contact' ? {scope: scope || 'UNBOUND', ...(name ? {raw_name: name} : {}), ...(secondary ? {raw_email: secondary} : {})}
      : {...(name ? {raw_name: name} : {}), ...(secondary ? {raw_account_code: secondary} : {})});
  }}><fieldset disabled={disabled}><div className="operational-form">
    <Field label="Match name" value={name} change={setName}/>
    <Field label={kind === 'contact' ? 'Match email' : 'Match Account Code'} value={secondary} change={setSecondary} maximum={kind === 'contact' ? 2048 : 512}/>
    {kind === 'contact' && <CustomerChooser label="Matching affiliation scope" value={scope} change={setScope}/>}
    <FormActions><Action icon="search" type="submit" disabled={!name.trim() && !secondary.trim()}>Find candidates</Action></FormActions>
  </div></fieldset></form>;
}
