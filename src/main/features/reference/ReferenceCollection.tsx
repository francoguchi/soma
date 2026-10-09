import {useCallback, useEffect, useId, useState, type ReactNode} from 'react';
import type * as C from '../../shared/api/generated/contracts';
import {api} from '../../shared/api/client';
import {BoundedCollection} from '../../shared/collections/BoundedCollection';
import {SelectableCollection} from '../../shared/collections/SelectableCollection';
import {SearchToolbar, type SearchSource} from '../../shared/components/CollectionSearch';
import {Action} from '../../shared/components/Section';
import {SomaIcon} from '../../shared/components/SomaIcon';
import {emptySelection} from '../../shared/interactions/selection';
import {AdvancedMatching, CandidateSummary, candidatePage, type MatchRequest, type ReferenceCollectionPage} from './components/Candidates';
import {Field, labels, page, paths, useOwnerQuery, type Kind, type Identity} from './model';

export type ClaimantLookup = {kind: Kind; code: string; token: number};
/** Browse, exact search and advanced matching share one retained collection and selection. */
export function ReferenceCollection({kind, refresh, currentId, open, toolbar, lookup}: {
  kind: Kind; refresh: number; currentId: string | null; open: (id: string) => void; toolbar?: ReactNode; lookup?: ClaimantLookup | null;
}) {
  const [selection, changeSelection] = useState(emptySelection);
  const [term, setTerm] = useState(''), [request, setRequest] = useState<MatchRequest | null>(null), [mode, setMode] = useState<'browse' | 'search' | 'advanced'>('browse');
  const [advanced, setAdvanced] = useState(false), [historical, setHistorical] = useState(''), [validation, setValidation] = useState('');
  const advancedId = useId(), key = kind + ':' + JSON.stringify(request);
  const sourceQuery = useOwnerQuery<C.ReferencePageTransportV1>(kind + refresh, signal => api.request('/api/v1/reference/' + paths[kind] + '?count_exact=true&limit=1', 'urn:soma:01:reference-page:v1', {signal}));
  const source: SearchSource = sourceQuery.loading ? 'loading' : sourceQuery.error !== null ? 'unavailable' : sourceQuery.value?.exact_count === 0 ? 'empty' : 'available';
  const defaultSource = source === 'available' && kind !== 'customer_organization' ? 'unavailable' : source;
  const reason = defaultSource === 'unavailable' && source === 'available' ? kind === 'contact'
    ? 'Name-or-email search is not supported yet. Use Advanced search within a Customer affiliation.'
    : 'Search is not available for Dispatch Locations.' : undefined;
  useEffect(() => {
    if (lookup?.kind === kind) {setRequest({raw_account_code: lookup.code}); setMode('advanced'); setAdvanced(false);}
  }, [lookup?.token]);
  useEffect(() => {if (currentId) setAdvanced(false);}, [currentId]);
  const load = useCallback(async (after: string | null, limit: number, signal: AbortSignal): Promise<ReferenceCollectionPage> => {
    if (request) return candidatePage(kind, request, after, limit, signal);
    const value = await api.request<C.ReferencePageTransportV1>('/api/v1/reference/' + paths[kind] + '?count_exact=true&limit=' + limit + (after ? '&after=' + encodeURIComponent(after) : ''), 'urn:soma:01:reference-page:v1', {signal});
    return page(value);
  }, [kind, key, refresh]);
  const clear = () => {setTerm(''); setRequest(null); setMode('browse'); setValidation('');};
  const search = () => {
    if (defaultSource !== 'available' || !term.trim()) return;
    if (new TextEncoder().encode(term).length > 512) {setValidation('This search term is too long. Use Advanced search for a longer exact name.'); return;}
    setRequest({raw_name: term, raw_account_code: term}); setMode('search'); setAdvanced(false); setValidation('');
  };
  return <div className="collection-navigator" data-collection-mode={mode}>
    <div className="collection-controls">{toolbar}<SearchToolbar label={'Search ' + labels[kind]} source={defaultSource} {...(reason ? {reason} : {})} value={term} change={setTerm} search={search} clear={clear} canClear={!!request || !!term} advanced={advanced} toggleAdvanced={() => setAdvanced(value => !value)} advancedId={advancedId}/>{validation && <p role="alert">{validation}</p>}</div>
    <div data-reference-records><BoundedCollection<Identity> retainQueries pageSize={50} queryKey={key} load={load} showCount={!request}
      emptyMessage={request ? '' : sourceQuery.value?.exact_count === 0 ? 'No ' + labels[kind] + ' yet.' : 'No active records on this page. Refresh to reload the list.'}
      summary={value => {
        const {evidence, criteria} = value as ReferenceCollectionPage;
        return <>{evidence && <>{mode === 'advanced' && criteria && <p className="console-comment">{[
          criteria['raw_name'] ? 'Name: ' + criteria['raw_name'] : '',
          criteria['raw_account_code'] ? 'Account Code: ' + criteria['raw_account_code'] : '',
          criteria['raw_email'] ? 'Email: ' + criteria['raw_email'] : '',
          criteria['scope'] ? 'Affiliation: ' + (criteria['scope'] === 'UNBOUND' ? 'Unbound' : 'selected Customer') : '',
        ].filter(Boolean).join(' · ')}</p>}<CandidateSummary evidence={evidence} countOnPage={value.items.length}/></>}{currentId && !value.items.some(row => row.reference_id === currentId) && <p className="console-comment">Opened record is outside this page.</p>}</>;
      }}
      render={(value, stale) => <SelectableCollection {...(currentId ? {currentId} : {})} columns={['Name', 'Revision']} rows={value.items.map(row => ({id: row.reference_id, cells: [row.name, row.revision], label: row.name, eligible: !stale && row.lifecycle_state === 'active', route: {type: kind, id: row.reference_id}}))} selection={selection} change={changeSelection} open={row => open(row.id)}/>}/></div>
    <section id={advancedId} hidden={!advanced} className="advanced-tool" aria-label="Advanced search">
      <h3><SomaIcon name="search"/> Advanced search</h3><AdvancedMatching kind={kind} disabled={source !== 'available'} submit={intent => {setRequest(intent); setMode('advanced'); setAdvanced(false); setValidation('');}}/>
      <details><summary><SomaIcon name="history"/> Open historical identity</summary><form className="operational-form" onSubmit={event => {event.preventDefault(); if (/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u.test(historical)) open(historical);}}>
        <Field label="Historical reference identity" value={historical} change={setHistorical} maximum={36} required/><Action type="submit">Open historical reference</Action>
      </form></details>
    </section>
  </div>;
}
