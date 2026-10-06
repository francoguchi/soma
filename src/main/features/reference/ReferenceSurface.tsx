import {useCallback, useRef, useState, type RefObject} from 'react';
import type * as C from '../../shared/api/generated/contracts';
import {api} from '../../shared/api/client';
import {SectionHeading, SectionTabs, ConsoleComment, Action} from '../../shared/components/Section';
import {SomaIcon} from '../../shared/components/SomaIcon';
import {RetainedContent} from '../../shared/components/RetainedContent';
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

function Records({kind, refresh, open, currentId}: {currentId: string | null; kind: Kind; refresh: number; open: (id: string) => void}) {
  const [selection, setSelection] = useState(emptySelection), [historical, setHistorical] = useState('');
  const load = useCallback(async (after: string | null, limit: number, signal: AbortSignal) => page(await api.request<C.ReferencePageTransportV1>('/api/v1/reference/' + paths[kind] + '?count_exact=true&limit=' + limit + (after ? '&after=' + encodeURIComponent(after) : ''), 'urn:soma:01:reference-page:v1', {signal})), [kind, refresh]);
  return <><BoundedCollection<C.ReferencePageTransportV1['items'][number]> pageSize={50} showEmptyCount={false} emptyMessage={'No ' + labels[kind] + ' yet.'} queryKey={kind} load={load} render={(value, stale) => <SelectableCollection {...(currentId ? {currentId} : {})} columns={['Name', 'Revision']} rows={value.items.map(row => ({id: row.reference_id, cells: [row.name, row.revision], label: row.name + ' · active · revision ' + row.revision, eligible: !stale, route: {type: kind, id: row.reference_id}}))} selection={selection} change={setSelection} open={row => open(row.id)}/>}/>
    <>{kind !== 'dispatch_location' && <details className="advanced-tool"><summary><SomaIcon name="search"/> Find by exact evidence</summary><Candidates kind={kind} open={open}/></details>}</><details className="advanced-tool"><summary><SomaIcon name="history"/> Open historical identity</summary><form className="operational-form" onSubmit={e => {e.preventDefault(); if (/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u.test(historical)) open(historical);}}><Field label="Historical reference identity" value={historical} change={setHistorical} maximum={36} required/><Action type="submit">Open historical reference</Action></form></details></>;
}
function RecordWork({kind, id, refresh, application, done, open, beginNew, cancel}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void; open: (id: string) => void; beginNew: boolean; cancel?: () => void}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  const draftIdentity = useRef(crypto.randomUUID());
  if (beginNew) return <Editor key={kind + draftIdentity.current} kind={kind} id={draftIdentity.current} detail={null} application={application} accepted={done} {...(cancel ? {cancel} : {})}/>;
  if (!id) return <p>Open a record explicitly, or create a new reference. Selecting a row alone does not open it.</p>;
  return <><QueryState query={query}/>{query.value && <><Editor key={kind + id} kind={kind} id={id} detail={query.value} application={application} accepted={done}/>{kind === 'customer_organization' && <AccountCode key={id} detail={query.value as C.ReferenceCustomerDetailV1} application={application} refresh={() => done(id)} open={open}/>}<Lifecycle kind={kind} detail={query.value} application={application} refresh={() => done(id)}/></>}</>;
}
function RecordEvidence({kind, id, refresh, application, done}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  if (!id) return <p>Opening a record reveals its immutable identity, lifecycle, revisions and bounded history.</p>;
  return <><QueryState query={query}/>{query.value && <><SectionHeading level={3} icon="identity">Identity</SectionHeading><dl className="compact-evidence"><dt>Name</dt><dd>{query.value.name}</dd><dt>State</dt><dd>{query.value.lifecycle_state}</dd><dt>Revision</dt><dd>{query.value.revision}</dd><dt>Created</dt><dd>{displayTime(query.value.created_at_utc)}</dd><dt>Updated</dt><dd>{displayTime(query.value.updated_at_utc)}</dd></dl><details className="advanced-tool"><summary><SomaIcon name="identity"/> Immutable identity</summary><code>{id}</code></details>{'current_address' in query.value && <section><SectionHeading level={3} icon="dispatch">Address source</SectionHeading><p>{query.value.current_address.source === 'SITE' ? 'Site-derived' : 'Standalone'} · {query.value.current_address.state}</p><p>{query.value.current_address.address_text ?? 'Current Site address is unavailable.'}</p></section>}{kind === 'contact' && <ContactEvidence key={id} detail={query.value as C.ReferenceContactDetailV1} application={application} refresh={() => done(id)}/>}<History kind={kind} id={id} revision={query.value.revision}/></>}</>;
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
  const singular = kind === 'customer_organization' ? 'Customer' : kind === 'contact' ? 'Contact' : 'Dispatch Location';
  const mode = id ? 'open' : creating ? 'create' : 'browse';
  const [collectionHost, setCollectionHost] = useState<HTMLDivElement | null>(null);
  const icon = kind === 'customer_organization' ? 'customer' : kind === 'contact' ? 'contact' : 'dispatch';
  const actions = <div role="group" aria-label="Collection actions" className="form-actions"><Action icon="add" variant="command" onClick={() => navigate('/settings/reference-data/' + kind + '/new')}>New {singular}</Action><Action icon="refresh" onClick={() => setRevision(v => v + 1)}>Refresh</Action></div>;
  return <div className="operational-surface" data-reference-mode={mode}>
    <SectionTabs label="Reference data types" secondary current={'/settings/reference-data/' + kind} navigate={navigate} items={(Object.keys(labels) as Kind[]).map(value => ({href: '/settings/reference-data/' + value, title: labels[value]}))}/>
    <RetainedContent host={collectionHost} restoreFocus={mode === 'browse'}><div data-reference-collection>
      {!id ? <><SectionHeading icon={icon} actions={actions}>{labels[kind]}</SectionHeading><ConsoleComment>Reusable {singular} identities available to SOMA workflows</ConsoleComment></> : actions}
      {(Object.keys(labels) as Kind[]).map(value => <div key={value} hidden={value !== kind}><Records currentId={value === kind ? id : null} kind={value} refresh={revision} open={target => navigate(referencePath(value, target))}/></div>)}
    </div></RetainedContent>
    {id ? <ConsolePanes label="Reference data pane" layout="workbench" focusRequest={{pane: 'work', token: path}} panes={[
      {id: 'records', title: labels[kind], content: <div ref={setCollectionHost}/>},
      {id: 'work', title: 'Details', content: <><Action icon="back" onClick={() => switchKind(kind)}>Back to list</Action><RecordWork key={kind + ':' + id} kind={kind} id={id} refresh={revision} application={application} done={done} open={open} beginNew={false}/></>},
      {id: 'evidence', title: 'Evidence & history', content: <RecordEvidence key={kind + ':' + id} kind={kind} id={id} refresh={revision} application={application} done={done}/>},
    ]}/> : creating ? <section className="content-section form-surface" data-create-surface><Action icon="back" onClick={() => switchKind(kind)}>Back to list</Action><SectionHeading icon={icon}>New {singular}</SectionHeading><ConsoleComment>Create a reusable {singular} reference</ConsoleComment><RecordWork key={kind + ':new'} kind={kind} id={null} refresh={revision} application={application} done={done} open={open} beginNew={true} cancel={() => switchKind(kind)}/></section> : <section className="content-section" aria-label={labels[kind]}><div ref={setCollectionHost}/></section>}
  </div>;
}
