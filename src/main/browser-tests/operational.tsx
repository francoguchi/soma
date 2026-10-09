// Synthetic data is test-only. No product owner/search/mutation is introduced.
import {useEffect, useId, useMemo, useRef, useState, type RefObject} from 'react';
import {createRoot} from 'react-dom/client';
import {OperationalFrame} from '../app/workspaces/OperationalFrame';
import {resolveRoute} from '../app/router';
import {OperatorStatus} from '../app/status/OperatorStatus';
import {useDiagnostics} from '../features/system/useDiagnostics';
import {api} from '../shared/api/client';
import type {BootstrapV1} from '../shared/api/generated/contracts';
import {OperationalLayout} from '../shared/components/OperationalLayout';
import {AdaptiveOverlay} from '../shared/components/AdaptiveOverlay';
import {SomaIcon} from '../shared/components/SomaIcon';
import {SearchToolbar} from '../shared/components/CollectionSearch';
import {SelectableCollection} from '../shared/collections/SelectableCollection';
import {BoundedCollection} from '../shared/collections/BoundedCollection';
import {emptySelection, type Selection} from '../shared/interactions/selection';
import {installScrollOwnership} from '../shared/interactions/scroll';
import {requestNavigation, useWorkingIntent, WorkingSurface} from '../shared/interactions/use-working-intent';
import '../styles/soma.css';

const dataset = Array.from({length:120}, (_, i) => ({id: 'record-' + i, name: 'Synthetic record ' + i, revision: 1}));
function Editor({name, target, application, accepted, formId}: {name: string; target: string; application: RefObject<HTMLElement | null>; accepted: (name: string) => void; formId: string}) {
  const intent = useWorkingIntent({name}, {contract_id:'OperationalEditV1',contract_version:1,target_type:'probe',target_id:target,scope_key:'edit',base_revision:'rev-1'}, application);
  return <form id={formId} onSubmit={event => {event.preventDefault(); if (!intent.conflict && intent.draft.name.trim()) {void intent.accepted().then(() => accepted(intent.draft.name));}}}>
    <label>Name<input aria-label="Record name" value={intent.draft.name} onChange={event => intent.edit('name', event.target.value)}/></label>
    <p>Synthetic acceptance changes this fixture session only.</p>{intent.recovery}
  </form>;
}
function CollectionFixture({scope, application, active = true}: {scope: string; application: RefObject<HTMLElement | null>; active?: boolean}) {
  const formId = useId();
  const [records, setRecords] = useState(dataset), [selection, setSelection] = useState<Selection>(emptySelection());
  const [editing, setEditing] = useState(false), [creating, setCreating] = useState(false), [focus, setFocus] = useState('');
  const [input, setInput] = useState(''), [query, setQuery] = useState(''), [advanced, setAdvanced] = useState(false), [tab, setTab] = useState('provenance'), [refresh, setRefresh] = useState(0);
  const selected = records.find(row => row.id === selection.selected_id);
  // This is the entire explicit synthetic population, never a product-page filter.
  const load = useMemo(() => async (cursor: string | null, limit: number, signal: AbortSignal) => {
    await new Promise(resolve => setTimeout(resolve, query === 'slow' ? 180 : 15));
    if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
    const matching = records.filter(row => !query || row.name === query), offset = cursor ? Number(cursor) : 0;
    return {items:matching.slice(offset, offset + limit),continuation:matching.length > offset + limit ? String(offset + limit) : null,total:matching.length,as_of_utc_s:1000,partial:false,warnings:[]};
  }, [query, records, refresh]);
  const reveal = (next: Selection) => {
    if (next.selected_id === selection.selected_id) {setSelection(next);return;}
    requestNavigation('select-record', () => {setSelection(next); setEditing(false); setCreating(false);});
  };
  const collection = {title:'Synthetic collection', actions:<div className="form-actions"><button onClick={() => requestNavigation('new-record', () => {setCreating(true); setEditing(false); setFocus(crypto.randomUUID());})}><SomaIcon name="add"/>New</button><button onClick={() => setRefresh(value => value + 1)}><SomaIcon name="refresh"/>Refresh</button>{selected && <button onClick={() => requestNavigation('clear-selection', () => {setSelection(emptySelection()); setEditing(false); setCreating(false);})}>Clear selection</button>}</div>,content:<>
    <SearchToolbar label="Exact synthetic name" source="available" value={input} change={setInput} search={() => setQuery(input)} clear={() => {setInput('');setQuery('');}} canClear={!!input || !!query} advanced={advanced} toggleAdvanced={() => setAdvanced(value => !value)} advancedId={'advanced-' + scope}/>
    <div id={'advanced-' + scope} hidden={!advanced}><p>Exact equality over the complete synthetic fixture population.</p></div>
    <BoundedCollection retainQueries queryKey={JSON.stringify([query,refresh])} load={load} render={(page, stale) => <SelectableCollection rows={page.items.map(row => ({...row,label:row.name,cells:[row.name,row.revision],eligible:!stale,route:{type:'probe',id:row.id}}))} columns={['Name','Revision']} selection={selection} change={reveal} open={row => requestNavigation('focus-inspector', () => {setSelection(previous => ({...previous,selected_id:row.id})); setEditing(false);setCreating(false);setFocus(crypto.randomUUID());})}/>}/>
  </>};
  const details = selected || creating ? {title:creating ? 'Creating' : editing ? 'Editor' : 'Details', actions:!editing && !creating ? <button aria-label="Edit selected record" title="Edit selected record" onClick={() => {setEditing(true);setFocus(crypto.randomUUID());}}><SomaIcon name="edit"/></button> : <div className="form-actions"><button type="submit" form={formId}>Save</button><button type="button" onClick={() => requestNavigation('cancel-edit', () => {setEditing(false);setCreating(false);})}>Cancel edit</button></div>,
    content:editing || creating ? <WorkingSurface active={active}><Editor formId={formId} key={creating ? 'new' : selected!.id} target={creating ? 'new-record' : selected!.id} name={creating ? '' : selected!.name} application={application} accepted={name => {
      if (creating) {const row = {id:crypto.randomUUID(),name,revision:1};setRecords(previous => [...previous,row]);setSelection(previous => ({...previous,selected_id:row.id}));}
      else setRecords(previous => previous.map(row => row.id === selected!.id ? {...row,name,revision:row.revision + 1} : row));
      setCreating(false);setEditing(false);
    }}/></WorkingSurface> : <dl className="compact-evidence"><dt>Name</dt><dd>{selected!.name}</dd><dt>State</dt><dd>Synthetic accepted record</dd><dt>Revision</dt><dd>{selected!.revision}</dd></dl>} : undefined;
  const context = selected && !creating ? {title:'Context',content:<><div className="form-actions" role="group" aria-label="Context tabs"><button aria-pressed={tab === 'provenance'} onClick={() => setTab('provenance')}>Provenance</button><button aria-pressed={tab === 'evidence'} onClick={() => setTab('evidence')}>Evidence</button></div>
    <div hidden={tab !== 'provenance'}><p>Source: complete in-memory synthetic fixture.</p><p>Identity: <code>{selected.id}</code></p><p>No relationship is accepted by inspection.</p></div>
    <div hidden={tab !== 'evidence'}><ol>{Array.from({length:40}, (_, i) => <li key={i}>Synthetic evidence {i} for {selected.id}</li>)}</ol></div></>} : undefined;
  return <OperationalLayout sessionKey={scope} collection={collection} {...(details ? {details} : {})} {...(context ? {context} : {})} focusRequest={focus}/>;
}
function Fixture() {
  const application = useRef<HTMLDivElement>(null), overlayApplication = useRef<HTMLDivElement>(null);
  const [bootstrap, setBootstrap] = useState<BootstrapV1 | null>(null), [path, setPath] = useState('/'), [overlay, setOverlay] = useState(false), [expanded, setExpanded] = useState(false);
  const [context, setContext] = useState('Records');
  const diagnostics = useDiagnostics(bootstrap?.run_id ?? null);
  useEffect(() => {
    void (async () => {let boot = await api.request<BootstrapV1>('/api/v1/bootstrap','bootstrap');api.acceptBootstrap(boot);
      if (boot.auth_state === 'setup_required') {await api.request('/api/v1/auth/setup','auth-result',{method:'POST',requestContract:'auth-setup-request',body:{run_id:api.runId,password:'Foundation fixture password 42',confirmation:'Foundation fixture password 42'}});boot = await api.request<BootstrapV1>('/api/v1/bootstrap','bootstrap');api.acceptBootstrap(boot);}setBootstrap(boot);})();
    return installScrollOwnership(document.documentElement, () => document.querySelector<HTMLElement>('[data-operational-pane][data-pane-active=true]:not([hidden]) [data-pane-body]'));
  }, []);
  const overlayRoute = (route: string) => {if (!resolveRoute(route)) throw new Error('Unknown route');setOverlay(true);setExpanded(route.startsWith('/settings/reference-data'));};
  if (!bootstrap) return <p>Preparing isolated native host</p>;
  return <><OperationalFrame caption="Foundation synthetic fixture" application={application} path={path} capabilities={bootstrap.capabilities} navigate={target => requestNavigation(target, () => setPath(target))} settings={() => overlayRoute('/settings/profile')}
    context={<><strong>Overview</strong>{['Records','Review'].map(value => <button key={value} aria-current={context === value ? 'page' : undefined} onClick={() => setContext(value)}>{value}</button>)}<button onClick={() => overlayRoute('/settings/reference-data/contact')}>Manage reference</button></>}
    status={<OperatorStatus bootstrap={bootstrap} diagnostics={diagnostics.value} unavailable={diagnostics.error !== null}/>}>
    <WorkingSurface active={!overlay}><CollectionFixture scope="overview-records" application={application} active={!overlay}/></WorkingSurface>
  </OperationalFrame>{overlay && <AdaptiveOverlay expanded={expanded} application={application} fallback={() => application.current?.querySelector('main') ?? null}
    close={() => requestNavigation('close-settings', () => setOverlay(false))} collapse={() => requestNavigation('collapse-settings', () => setExpanded(false))}
    compact={<><p>Profile and Appearance — synthetic preview</p><label>Display name<input defaultValue="Local Administrator"/></label><label>Appearance<select defaultValue="core_dark"><option value="core_dark">SOMA Core Dark</option></select></label><button onClick={() => overlayRoute('/settings/reference-data/contact')}>Reference data</button></>}
    manager={<div ref={overlayApplication} className="overlay-content"><WorkingSurface active={expanded}><CollectionFixture scope="reference-synthetic" application={overlayApplication} active={expanded}/></WorkingSurface></div>}/>}</>;
}
createRoot(document.getElementById('operational-root')!).render(<Fixture/>);
