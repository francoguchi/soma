import {SectionHeading} from '../../../shared/components/Section';
import {useCallback} from 'react';
import type * as C from '../../../shared/api/generated/contracts';
import {BoundedCollection} from '../../../shared/collections/BoundedCollection';
import {api} from '../../../shared/api/client';
import {displayTime} from '../../../shared/time';
import {identityPage, page, type Kind} from '../model';

type Entry = {id: string; text: string; opened: number; closed: number | null};
export function History({kind, id, revision}: {kind: Kind; id: string; revision: number}) {
  const load = useCallback(async (after: string | null, limit: number, signal: AbortSignal) => {
    const query = '?count_exact=true&limit=' + limit + (after ? '&after=' + encodeURIComponent(after) : '');
    if (kind === 'customer_organization') {
      const value = await api.request<C.ReferenceAccountCodePageV1>('/api/v1/reference/customer-organizations/' + id + '/customer-account-code/history' + query, 'urn:soma:01:account-code-page:v1', {signal});
      return {...page(value), items: value.items.map(row => ({id: row.customer_org_identifier_id, text: row.value_text + ' · ' + row.lifecycle_state, opened: row.created_at_utc, closed: row.superseded_at_utc}))};
    }
    const value = await api.request<C.ReferenceAffiliationPageV1>('/api/v1/reference/contacts/' + id + '/affiliation-history' + query, 'urn:soma:01:affiliation-page:v1', {signal});
    const names = await identityPage('customer_organization', [...new Set(value.items.map(row => row.customer_org_id))], signal);
    return {...page(value), items: value.items.map(row => ({id: row.contact_affiliation_id, text: (names.items.find(name => name.reference_id === row.customer_org_id)?.name ?? 'Historical Customer') + (row.is_current ? ' · current' : ' · closed'), opened: row.opened_at_utc, closed: row.closed_at_utc}))};
  }, [kind, id, revision]);
  if (kind === 'dispatch_location') return null;
  return <section><SectionHeading level={3} icon="history">{kind === 'contact' ? 'Affiliation history' : 'Account Code history'}</SectionHeading><BoundedCollection<Entry> pageSize={50} queryKey={kind + id + revision} load={load} emptyMessage="No preserved history yet." render={value => <ul className="evidence-list">{value.items.map(row => <li key={row.id}><strong>{row.text}</strong><p>Opened {displayTime(row.opened)}{row.closed !== null && <> · closed {displayTime(row.closed)}</>}</p><details><summary>History identity</summary><code>{row.id}</code></details></li>)}</ul>}/></section>;
}
