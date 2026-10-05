import {useCallback, useRef, useState, type RefObject} from 'react';
import type * as C from '../../shared/api/generated/contracts';
import {api} from '../../shared/api/client';
import {ConsolePanes} from '../../shared/components/ConsolePanes';
import {BoundedCollection} from '../../shared/collections/BoundedCollection';
import {SelectableCollection} from '../../shared/collections/SelectableCollection';
import {emptySelection} from '../../shared/interactions/selection';
import {displayTime} from '../../shared/time';
import {Candidates} from './components/Candidates';
import {Lifecycle} from './components/Lifecycle';
import {History} from './components/History';
import {AccountCode} from './customer/AccountCode';
import {ContactEvidence} from './contact/ContactEvidence';
import {Editor} from './Editor';
import {Field, QueryState, labels, paths, page, readDetail, referencePath, useOwnerQuery, type Kind, type Detail} from './model';

function Records({kind, refresh, open}: {kind: Kind; refresh: number; open: (id: string) => void}) {
  const [selection, setSelection] = useState(emptySelection), [historical, setHistorical] = useState('');
  const load = useCallback(async (after: string | null, limit: number, signal: AbortSignal) => page(await api.request<C.ReferencePageTransportV1>('/api/v1/reference/' + paths[kind] + '?count_exact=true&limit=' + limit + (after ? '&after=' + encodeURIComponent(after) : ''), 'urn:soma:01:reference-page:v1', {signal})), [kind, refresh]);
  return <><BoundedCollection<C.ReferencePageTransportV1['items'][number]> pageSize={50} queryKey={kind} load={load} render={(value, stale) => <SelectableCollection rows={value.items.map(row => ({id: row.reference_id, label: row.name + ' · active · revision ' + row.revision, eligible: !stale, route: {type: kind, id: row.reference_id}}))} selection={selection} change={setSelection} open={row => open(row.id)}/>}/>
    <details><summary>Open a historical identity</summary><form className="operational-form" onSubmit={e => {e.preventDefault(); if (/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u.test(historical)) open(historical);}}><Field label="Historical reference identity" value={historical} change={setHistorical} maximum={36} required/><button>Open historical reference</button></form></details></>;
}
function RecordWork({kind, id, refresh, application, done, open, beginNew}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void; open: (id: string) => void; beginNew: boolean}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  const draftIdentity = useRef(crypto.randomUUID());
  if (beginNew) return <Editor key={kind + draftIdentity.current} kind={kind} id={draftIdentity.current} detail={null} application={application} accepted={done}/>;
  if (!id) return <p>Open a record explicitly, or create a new reference. Selecting a row alone does not open it.</p>;
  return <><QueryState query={query}/>{query.value && <><Editor key={kind + id} kind={kind} id={id} detail={query.value} application={application} accepted={done}/>{kind === 'customer_organization' && <AccountCode key={id} detail={query.value as C.ReferenceCustomerDetailV1} application={application} refresh={() => done(id)} open={open}/>}<Lifecycle kind={kind} detail={query.value} application={application} refresh={() => done(id)}/></>}</>;
}
function RecordEvidence({kind, id, refresh, application, done}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  if (!id) return <p>Opening a record reveals its immutable identity, lifecycle, revisions and bounded history.</p>;
  return <><QueryState query={query}/>{query.value && <><dl><dt>Name</dt><dd>{query.value.name}</dd><dt>State</dt><dd>{query.value.lifecycle_state}</dd><dt>Revision</dt><dd>{query.value.revision}</dd><dt>Created</dt><dd>{displayTime(query.value.created_at_utc)}</dd><dt>Updated</dt><dd>{displayTime(query.value.updated_at_utc)}</dd></dl><details><summary>Immutable identity</summary><code>{id}</code></details>{'current_address' in query.value && <section><h3>Address source</h3><p>{query.value.current_address.source === 'SITE' ? 'Site-derived' : 'Standalone'} · {query.value.current_address.state}</p><p>{query.value.current_address.address_text ?? 'Current Site address is unavailable.'}</p></section>}{kind === 'contact' && <ContactEvidence key={id} detail={query.value as C.ReferenceContactDetailV1} application={application} refresh={() => done(id)}/>}<History kind={kind} id={id} revision={query.value.revision}/></>}</>;
}
export function ReferenceSurface({path, navigate, application}: {path: string; navigate: (path: string) => void; application: RefObject<HTMLElement | null>}) {
  const [, , , rawKind, rawId] = path.split('/');
  const kind: Kind = rawKind === 'contact' || rawKind === 'dispatch_location' ? rawKind : 'customer_organization';
  const id = rawId && rawId !== 'new' ? rawId : null;
  const creating = rawId === 'new';
  const [revision, setRevision] = useState(0);
  const open = (target: string) => navigate(referencePath(kind, target));
  const done = (target: string) => {setRevision(v => v + 1); if (target !== id) navigate(referencePath(kind, target));};
  const switchKind = (next: Kind) => navigate('/settings/reference-data/' + next);
  return <div className="operational-surface"><div className="action-strip" role="group" aria-label="Reference data types">{(Object.keys(labels) as Kind[]).map(value => <button key={value} aria-pressed={kind === value} onClick={() => switchKind(value)}>{labels[value]}</button>)}<button onClick={() => navigate('/settings/reference-data/' + kind + '/new')}>New {kind === 'customer_organization' ? 'Customer' : kind === 'contact' ? 'Contact' : 'Dispatch Location'}</button><button onClick={() => setRevision(v => v + 1)}>Refresh current state</button></div>
    <ConsolePanes label="Reference data pane" layout="workbench" focusRequest={{pane: id || creating ? 'work' : 'records', token: path}} panes={[
      {id: 'records', title: labels[kind], content: <>{(Object.keys(labels) as Kind[]).map(value => <div key={value} hidden={value !== kind}><Records kind={value} refresh={revision} open={target => navigate(referencePath(value, target))}/></div>)}<Candidates key={kind} kind={kind} open={open}/></>},
      {id: 'work', title: creating ? 'New reference' : 'Reference work', content: <RecordWork key={kind + ':' + (id ?? rawId ?? '')} kind={kind} id={id} refresh={revision} application={application} done={done} open={open} beginNew={creating}/>},
      {id: 'evidence', title: 'Context and history', content: <RecordEvidence key={kind + ':' + id} kind={kind} id={id} refresh={revision} application={application} done={done}/>},
    ]}/>
  </div>;
}
