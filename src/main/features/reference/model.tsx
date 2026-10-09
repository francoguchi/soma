import {useEffect, useId, useRef, useState, type ReactNode} from 'react';
import {api, ApiError, ApiInputError, QueryController} from '../../shared/api/client';
import type * as C from '../../shared/api/generated/contracts';
import type {Page} from '../../shared/collections/BoundedCollection';
import {ErrorState} from '../../shared/components/ErrorState';

export type Kind = 'customer_organization' | 'contact' | 'dispatch_location';
export const labels: Record<Kind, string> = {customer_organization: 'Customers', contact: 'Contacts', dispatch_location: 'Dispatch Locations'};
export const paths: Record<Kind, string> = {customer_organization: 'customer-organizations', contact: 'contacts', dispatch_location: 'dispatch-locations'};
export type Detail = C.ReferenceCustomerDetailV1 | C.ReferenceContactDetailV1 | C.ReferenceDispatchDetailV1;
export type Identity = C.ReferenceIdentitiesResultV1['items'][number];
export function referencePath(kind: Kind, id: string) {return '/settings/reference-data/' + kind + '/' + encodeURIComponent(id);}
export function readDetail(kind: Kind, id: string, signal?: AbortSignal): Promise<Detail> {
  const contract = {customer_organization: 'customer-detail', contact: 'contact-detail', dispatch_location: 'dispatch-detail'}[kind];
  return api.request('/api/v1/reference/' + paths[kind] + '/' + encodeURIComponent(id), 'urn:soma:01:' + contract + ':v1', {...(signal ? {signal} : {})});
}
export function identityPage(kind: Kind, ids: readonly string[], signal?: AbortSignal): Promise<C.ReferenceIdentitiesResultV1> {
  return api.request('/api/v1/reference/identities', 'urn:soma:01:identities-result:v1', {method: 'POST', body: {reference_type: kind, ids}, requestContract: 'urn:soma:01:identities-request:v1', ...(signal ? {signal} : {})});
}
export function page<T>(value: {items: readonly T[]; continuation: string | null; exact_count: number | null; as_of_utc_s: number}): Page<T> {
  return {...value, partial: false, warnings: [], total: value.exact_count};
}
export function useOwnerQuery<T>(key: string, load: (signal: AbortSignal) => Promise<T>) {
  const loader = useRef(load); loader.current = load;
  const [value, setValue] = useState<T | null>(null), [error, setError] = useState<unknown>(null), [loading, setLoading] = useState(true), [retry, setRetry] = useState(0);
  useEffect(() => {
    const query = new QueryController<T>(); setLoading(true); setError(null);
    void query.query(signal => loader.current(signal), v => {setValue(v); setLoading(false);}, e => {setError(e); setLoading(false);});
    return () => query.cancel();
  }, [key, retry]);
  return {value, error, loading, reload: () => setRetry(v => v + 1)};
}
export function QueryState({query}: {query: {error: unknown; loading: boolean; reload: () => void}}) {
  return <>{query.loading && <p role="status">Loading current evidence. Previous evidence, if shown, is stale.</p>}{query.error !== null && <ErrorState error={query.error} retry={query.reload}/>}</>;
}
export function useOwnerAction() {
  const [error, setError] = useState<unknown>(null), [busy, setBusy] = useState(false), [message, setMessage] = useState('');
  const active = useRef(false), attempt = useRef<{key: string; command: string; send: (command: string) => Promise<unknown>; done: () => void | Promise<void>} | null>(null);
  async function run(key: string, send: (command: string) => Promise<unknown>, done: () => void | Promise<void>) {
    if (active.current) return false;
    if (attempt.current && attempt.current.key !== key) {setError(new Error('Retry the pending operation with its original values before changing this action.')); return false;}
    const command = attempt.current?.command ?? crypto.randomUUID();
    attempt.current ??= {key, command, send, done};
    const captured = attempt.current;
    active.current = true; setBusy(true); setError(null); setMessage('');
    try {const result = await captured.send(command); attempt.current = null; setMessage(result && typeof result === 'object' && 'outcome' in result ? result.outcome === 'NO_CHANGE' ? 'No change; operation recorded.' : 'Operation accepted.' : 'Current evidence loaded.'); await captured.done(); return true;}
    catch (caught) {setError(caught); if (caught instanceof ApiInputError || caught instanceof ApiError && caught.detail.code !== 'INTERNAL_ERROR') attempt.current = null; return false;}
    finally {active.current = false; setBusy(false);}
  }
  return {run, busy, pending: attempt.current !== null, error, feedback: <>{message && <p role="status">{message}</p>}{error !== null && <ErrorState error={error}/>} {error !== null && attempt.current && <button disabled={busy} onClick={() => {const captured = attempt.current; if (captured) void run(captured.key, captured.send, captured.done);}}>Retry exact pending operation</button>}</>};
}
export function Field({label, value, change, multiline = false, disabled = false, required = false, maximum = 1024}: {label: string; value: string; change: (value: string) => void; multiline?: boolean; disabled?: boolean; required?: boolean; maximum?: number}) {
  const id = useId(), bytes = new TextEncoder().encode(value).length;
  return <div className="form-field"><label htmlFor={id}>{label}</label>{multiline ? <textarea id={id} aria-describedby={bytes > maximum ? id + '-bound' : undefined} value={value} disabled={disabled} required={required} rows={4} onChange={e => change(e.target.value)}/> : <input id={id} aria-describedby={bytes > maximum ? id + '-bound' : undefined} value={value} disabled={disabled} required={required} onChange={e => change(e.target.value)}/>} {bytes > maximum && <small id={id + '-bound'} role="alert">Shorten this value before saving. {bytes} UTF-8 bytes exceeds the {maximum}-byte field bound.</small>}</div>;
}
export function Section({title, children}: {title: string; children: ReactNode}) {return <section><h3>{title}</h3>{children}</section>;}

export function CustomerChooser({value, change, label = 'Customer', allowUnbound = true, disabled = false}: {value: string; change: (id: string) => void; label?: string; allowUnbound?: boolean; disabled?: boolean}) {
  const [after, setAfter] = useState<string | null>(null);
  const query = useOwnerQuery<C.ReferencePageTransportV1>(String(after), signal => api.request('/api/v1/reference/customer-organizations?limit=50' + (after ? '&after=' + encodeURIComponent(after) : ''), 'urn:soma:01:reference-page:v1', {signal}));
  const selected = useOwnerQuery(value, signal => value ? identityPage('customer_organization', [value], signal) : Promise.resolve({items: []}));
  return <div><label>{label}<select value={value} disabled={disabled || query.loading} onChange={e => change(e.target.value)}>
    <option value="">{allowUnbound ? 'Unbound' : 'Choose a Customer explicitly'}</option>
    {value && !query.value?.items.some(row => row.reference_id === value) && <option value={value}>{selected.value?.items[0]?.name ?? 'Selected Customer'}{selected.value?.items[0]?.lifecycle_state === 'archived' ? ' (archived)' : ''}</option>}
    {query.value?.items.map(row => <option key={row.reference_id} value={row.reference_id}>{row.name}</option>)}
  </select></label><QueryState query={query}/>{query.value?.continuation && <button type="button" disabled={disabled} onClick={() => setAfter(query.value!.continuation)}>More Customers</button>}{after && <button type="button" onClick={() => setAfter(null)}>First Customer page</button>}</div>;
}
