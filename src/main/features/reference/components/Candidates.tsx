import {useCallback, useState} from 'react';
import {api} from '../../../shared/api/client';
import type * as C from '../../../shared/api/generated/contracts';
import {BoundedCollection, type Page} from '../../../shared/collections/BoundedCollection';
import {SelectableCollection} from '../../../shared/collections/SelectableCollection';
import {emptySelection, type Selection} from '../../../shared/interactions/selection';
import {CustomerChooser, Field, identityPage, labels, type Kind, type Identity} from '../model';

type CandidatePage = Page<Identity> & {evidence: C.ReferenceCandidateResultV1};
export function Candidates({kind, open, accountCode}: {kind: Kind; open: (id: string) => void; accountCode?: string}) {
  const [name, setName] = useState(''), [secondary, setSecondary] = useState(accountCode ?? ''), [scope, setScope] = useState('');
  const [request, setRequest] = useState<Record<string, string> | null>(accountCode ? {raw_account_code: accountCode} : null);
  const [selection, setSelection] = useState<Selection>(emptySelection);
  const key = JSON.stringify(request);
  const load = useCallback(async (after: string | null, limit: number, signal: AbortSignal): Promise<CandidatePage> => {
    const suffix = kind === 'customer_organization' ? 'customer-organization' : 'contact';
    const evidence = await api.request<C.ReferenceCandidateResultV1>('/api/v1/reference/match/' + suffix, 'urn:soma:01:candidate-result:v1', {method: 'POST', body: {...request, limit, ...(after ? {after} : {})}, requestContract: 'urn:soma:01:match-' + (kind === 'contact' ? 'contact' : 'customer') + '-request:v1', signal});
    const details = await identityPage(kind, evidence.candidate_ids, signal);
    return {evidence, items: details.items, continuation: evidence.continuation, total: evidence.candidate_count, as_of_utc_s: 0, warnings: [], partial: false};
  }, [key, kind]);
  if (kind === 'dispatch_location') return null;
  return <section><h3>Find {labels[kind].toLowerCase()} by exact evidence</h3>{!accountCode && <form className="operational-form" onSubmit={e => {e.preventDefault(); setRequest(kind === 'contact' ? {scope: scope || 'UNBOUND', ...(name ? {raw_name: name} : {}), ...(secondary ? {raw_email: secondary} : {})} : {...(name ? {raw_name: name} : {}), ...(secondary ? {raw_account_code: secondary} : {})});}}>
    <Field label="Match name" value={name} change={setName}/><Field label={kind === 'contact' ? 'Match email' : 'Match Account Code'} value={secondary} change={setSecondary} maximum={kind === 'contact' ? 2048 : 512}/>
    {kind === 'contact' && <CustomerChooser label="Matching affiliation scope" value={scope} change={setScope}/>}
    <button>Find candidates</button>
  </form>}{request && <BoundedCollection<Identity> pageSize={50} queryKey={kind + key} load={load} emptyMessage="UNRESOLVED — no exact candidates. Create or select a reference explicitly." render={raw => {
    const {evidence} = raw as CandidatePage;
    return <><p role="status">{evidence.state} · {evidence.candidate_count} exact candidates</p><p>{evidence.explanation.replaceAll('_', ' ')}</p><p>Account Code evidence and descriptive-name evidence are independent. Opening a candidate does not accept a link or merge.</p><SelectableCollection rows={raw.items.map(row => ({id: row.reference_id, label: row.name + ' · revision ' + row.revision, eligible: row.lifecycle_state === 'active', route: {type: kind, id: row.reference_id}}))} selection={selection} change={setSelection} open={row => open(row.id)}/></>;
  }}/>}{accountCode && <p>Multiple claims are ambiguous reviewed external evidence, not unique Customer ownership.</p>}</section>;
}
