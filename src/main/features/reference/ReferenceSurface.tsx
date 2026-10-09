import {useRef, useState, type RefObject} from 'react';
import type * as C from '../../shared/api/generated/contracts';
import {SectionHeading, SectionTabs, ConsoleComment, Action} from '../../shared/components/Section';
import {SomaIcon} from '../../shared/components/SomaIcon';
import {RetainedContent} from '../../shared/components/RetainedContent';
import {ConsolePanes} from '../../shared/components/ConsolePanes';
import {displayTime} from '../../shared/time';
import {Lifecycle} from './components/Lifecycle';
import {History} from './components/History';
import {AccountCode} from './customer/AccountCode';
import {ContactEvidence} from './contact/ContactEvidence';
import {Editor} from './Editor';
import {ReferenceCollection, type ClaimantLookup} from './ReferenceCollection';
import {QueryState, labels, readDetail, referencePath, useOwnerQuery, type Kind, type Detail} from './model';

function RecordWork({kind, id, refresh, application, done, open, beginNew, cancel, showClaimants}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void; open: (id: string) => void; beginNew: boolean; cancel?: () => void; showClaimants: (code: string) => void}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  const draftIdentity = useRef(crypto.randomUUID());
  if (beginNew) return <Editor key={kind + draftIdentity.current} kind={kind} id={draftIdentity.current} detail={null} application={application} accepted={done} {...(cancel ? {cancel} : {})}/>;
  if (!id) return <p>Open a record explicitly, or create a new reference. Selecting a row alone does not open it.</p>;
  return <><QueryState query={query}/>{query.value && <><Editor key={kind + id} kind={kind} id={id} detail={query.value} application={application} accepted={done}/>{kind === 'customer_organization' && <AccountCode key={id} detail={query.value as C.ReferenceCustomerDetailV1} application={application} refresh={() => done(id)} showClaimants={showClaimants}/>}<Lifecycle kind={kind} detail={query.value} application={application} refresh={() => done(id)}/></>}</>;
}
function RecordEvidence({kind, id, refresh, application, done}: {kind: Kind; id: string | null; refresh: number; application: RefObject<HTMLElement | null>; done: (id: string) => void}) {
  const query = useOwnerQuery<Detail | null>(kind + id + refresh, signal => id ? readDetail(kind, id, signal) : Promise.resolve(null));
  if (!id) return <p>Opening a record reveals its immutable identity, lifecycle, revisions and bounded history.</p>;
  return <><QueryState query={query}/>{query.value && <><SectionHeading level={3} icon="identity">Identity</SectionHeading><dl className="compact-evidence"><dt>State</dt><dd>{query.value.lifecycle_state}</dd><dt>Revision</dt><dd>{query.value.revision}</dd><dt>Created</dt><dd>{displayTime(query.value.created_at_utc)}</dd><dt>Updated</dt><dd>{displayTime(query.value.updated_at_utc)}</dd></dl><details className="advanced-tool"><summary><SomaIcon name="identity"/> Immutable identity</summary><code>{id}</code></details>{'current_address' in query.value && <section><SectionHeading level={3} icon="dispatch">Address source</SectionHeading><p>{query.value.current_address.source === 'SITE' ? 'Site-derived' : 'Standalone'} · {query.value.current_address.state}</p><p>{query.value.current_address.address_text ?? 'Current Site address is unavailable.'}</p></section>}{kind === 'contact' && <ContactEvidence key={id} detail={query.value as C.ReferenceContactDetailV1} application={application} refresh={() => done(id)}/>}<History kind={kind} id={id} revision={query.value.revision}/></>}</>;
}
export function ReferenceSurface({path, navigate, application}: {path: string; navigate: (path: string) => void; application: RefObject<HTMLElement | null>}) {
  const [, , , rawKind, rawId] = path.split('/');
  const kind: Kind = rawKind === 'contact' || rawKind === 'dispatch_location' ? rawKind : 'customer_organization';
  const id = rawId && rawId !== 'new' ? rawId : null;
  const creating = rawId === 'new';
  const [revision, setRevision] = useState(0);
  const [lookup, setLookup] = useState<ClaimantLookup | null>(null);
  const showClaimants = (code: string) => setLookup(previous => ({kind, code, token: (previous?.token ?? 0) + 1}));
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
    {id && <div className="form-actions" data-reference-navigation><Action icon="back" onClick={() => switchKind(kind)}>Back to list</Action></div>}
    <RetainedContent host={collectionHost} restoreFocus={mode === 'browse'}><div data-reference-collection>
      {(Object.keys(labels) as Kind[]).map(value => <div key={value} hidden={value !== kind}><ReferenceCollection currentId={value === kind ? id : null} kind={value} refresh={revision} lookup={lookup} toolbar={!id ? <SectionHeading icon={icon} actions={actions}>{labels[kind]}</SectionHeading> : actions} open={target => navigate(referencePath(value, target))}/></div>)}
    </div></RetainedContent>
    {id ? <ConsolePanes label="Reference data pane" layout="workbench" focusRequest={{pane: 'work', token: path}} panes={[
      {id: 'records', title: labels[kind], content: <div ref={setCollectionHost}/>},
      {id: 'work', title: 'Details', content: <RecordWork key={kind + ':' + id} kind={kind} id={id} refresh={revision} application={application} done={done} open={open} beginNew={false} showClaimants={showClaimants}/>},
      {id: 'evidence', title: 'Evidence & history', content: <RecordEvidence key={kind + ':' + id} kind={kind} id={id} refresh={revision} application={application} done={done}/>},
    ]}/> : creating ? <section className="content-section form-surface" data-create-surface><SectionHeading icon={icon}>New {singular}</SectionHeading><ConsoleComment>Create a reusable {singular} reference</ConsoleComment><RecordWork key={kind + ':new'} kind={kind} id={null} refresh={revision} application={application} done={done} open={open} beginNew={true} showClaimants={showClaimants} cancel={() => switchKind(kind)}/></section> : <section className="content-section" aria-label={labels[kind]}><div ref={setCollectionHost}/></section>}
  </div>;
}
