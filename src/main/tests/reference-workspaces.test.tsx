import {useRef, useState} from 'react';
import {afterEach, expect, test, vi} from 'vitest';
import {cleanup, fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import {api, ApiError, ApiInputError, ApiClient} from '../shared/api/client';
import {resolveRoute} from '../app/router';
import {ReferenceCollection} from '../features/reference/ReferenceCollection';
import {Field, useOwnerAction} from '../features/reference/model';
import {useWorkingIntent} from '../shared/interactions/use-working-intent';
import {AppearancePreference} from '../shared/appearance-preference';
import {Lifecycle} from '../features/reference/components/Lifecycle';
import {ReferenceSurface} from '../features/reference/ReferenceSurface';
import {SelectableCollection} from '../shared/collections/SelectableCollection';
import {emptySelection} from '../shared/interactions/selection';

afterEach(() => {cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals();});
const id = '4d204e28-3a66-43cb-81ca-a31cc94c9b11';
const notFound = () => new ApiError({code: 'WORKING_COPY_NOT_FOUND', summary: 'No copy.', recoverability: 'none', safe_next_action: null, correlation_id: id});

test('contextual reference routes remain under Settings and reject unknown or injected paths', () => {
  expect(resolveRoute('/settings/reference-data/contact/' + id)?.capability).toBe('settings');
  expect(resolveRoute('/settings/reference-data/dispatch_location/new')?.title).toBe('Settings');
  for (const path of ['/customers', '/settings/reference-data/contacts', '/settings/reference-data/contact/invalid', '/settings/reference-data/contact/' + id + '/delete']) expect(resolveRoute(path)).toBeNull();
});

test('an exact unique candidate is evidence and opens only after explicit activation', async () => {
  vi.spyOn(api, 'request').mockImplementation(async path => (path.endsWith('/identities') ? {items: [{reference_id: id, name: 'Customer', lifecycle_state: 'active', revision: 1}]} : path.includes('/match/') ? {candidate_ids: [id], state: 'UNIQUE_CANDIDATE', candidate_count: 1, explanation: 'ACCOUNT_CODE_MATCH', continuation: null} : {items: [{reference_id: id, name: 'Customer', lifecycle_state: 'active', revision: 1}], exact_count: 1, continuation: null, as_of_utc_s: 0}) as never);
  const open = vi.fn();
  render(<ReferenceCollection kind="customer_organization" refresh={0} currentId={null} open={open}/>);
  await waitFor(() => expect(screen.getByRole('search').getAttribute('data-search-source')).toBe('available'));
  fireEvent.click(screen.getByRole('button', {name: 'Advanced search'}));
  fireEvent.change(screen.getByLabelText('Match Account Code'), {target: {value: 'CODE'}});
  fireEvent.click(screen.getByRole('button', {name: 'Find candidates'}));
  await screen.findByText('Unique candidate · 1 exact candidate');
  expect(screen.getByText(/Matched by Account Code/)).toBeTruthy();
  expect(screen.getAllByRole('grid')).toHaveLength(1);
  expect(screen.queryByText('1 record')).toBeNull();
  expect(screen.getByRole('button', {name: 'Advanced search'}).getAttribute('aria-expanded')).toBe('false');
  expect(open).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', {name: 'Open Customer'}).closest('[role=row]')!);
  expect(open).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', {name: 'Open Customer'}));
  expect(open).toHaveBeenCalledExactlyOnceWith(id);
});

test.each([0, 7])('search uses the authoritative count (%i), not the current empty page', async count => {
  vi.spyOn(api, 'request').mockResolvedValue({items: [], continuation: null, exact_count: count, as_of_utc_s: 0} as never);
  function Fixture() {const root = useRef<HTMLDivElement>(null); return <div ref={root}><ReferenceSurface path="/settings/reference-data/customer_organization" navigate={() => {}} application={root}/></div>;}
  render(<Fixture/>);
  await waitFor(() => expect(screen.getByRole('search', {name: 'Search Customers'}).getAttribute('data-search-source')).toBe(count === 0 ? 'empty' : 'available'));
  const input = within(screen.getByRole('search', {name: 'Search Customers'})).getByRole('textbox', {name: 'Search Customers'}) as HTMLInputElement;
  expect(input.matches(':disabled')).toBe(count === 0);
  if (count === 0) expect(screen.getByRole('search', {name: 'Search Customers'}).textContent).toContain('No active records to search yet.');
  else {fireEvent.change(input, {target: {value: 'Beyond this page'}}); expect((within(screen.getByRole('search', {name: 'Search Customers'})).getByRole('button', {name: 'Search'}) as HTMLButtonElement).matches(':disabled')).toBe(false);}
});

test('an unavailable source exposes a reason and disables owner search without a local fallback', async () => {
  const request = vi.spyOn(api, 'request').mockRejectedValue(new Error('Unavailable'));
  function Fixture() {const root = useRef<HTMLDivElement>(null); return <div ref={root}><ReferenceSurface path="/settings/reference-data/customer_organization" navigate={() => {}} application={root}/></div>;}
  render(<Fixture/>);
  await waitFor(() => expect(screen.getByRole('search', {name: 'Search Customers'}).getAttribute('data-search-source')).toBe('unavailable'));
  expect((within(screen.getByRole('search', {name: 'Search Customers'})).getByRole('textbox', {name: 'Search Customers'}) as HTMLInputElement).matches(':disabled')).toBe(true);
  expect(screen.getByRole('search', {name: 'Search Customers'}).textContent).toContain('Search is unavailable.');
  expect(request.mock.calls.some(call => call[0].includes('/match/'))).toBe(false);
});

test('default search changes the one collection with owner union evidence and clear restores browsing', async () => {
  const row = {reference_id: id, name: 'Customer', lifecycle_state: 'active', revision: 1};
  const request = vi.spyOn(api, 'request').mockImplementation(async path => (path.endsWith('/identities') ? {items: []} : path.includes('/match/') ? {candidate_ids: [], state: 'UNRESOLVED', candidate_count: 0, explanation: 'NO_CANONICAL_CANDIDATE', continuation: null} : {items: [row], exact_count: 1, continuation: null, as_of_utc_s: 0}) as never);
  render(<ReferenceCollection kind="customer_organization" refresh={0} currentId={null} open={() => {}}/>);
  await screen.findByText('1 record');
  const input = screen.getByRole('textbox', {name: 'Search Customers'});
  fireEvent.change(input, {target: {value: 'Missing'}});
  fireEvent.click(screen.getByRole('button', {name: 'Search'}));
  await screen.findByText('No exact candidates');
  expect(screen.queryByRole('button', {name: 'Open Customer'})).toBeNull();
  expect(document.body.textContent).not.toMatch(/0 records|0 matching|0 exact/u);
  expect(request.mock.calls.find(call => call[0].includes('/match/'))?.[2]?.body).toEqual({raw_name: 'Missing', raw_account_code: 'Missing', limit: 50});
  expect(input.matches(':disabled')).toBe(false);
  fireEvent.click(screen.getByRole('button', {name: 'Clear search'}));
  await screen.findByText('1 record');
  expect(screen.getAllByRole('grid')).toHaveLength(1);
});

test('default Contact and Dispatch search disclose contract gaps while advanced Contact matching remains available', async () => {
  vi.spyOn(api, 'request').mockResolvedValue({items: [], exact_count: 1, continuation: null, as_of_utc_s: 0} as never);
  const view=render(<ReferenceCollection kind="contact" refresh={0} currentId={null} open={() => {}}/>);
  await screen.findByText(/Name-or-email search is not supported/);
  expect(screen.getByRole('textbox', {name: 'Search Contacts'}).matches(':disabled')).toBe(true);
  fireEvent.click(screen.getByRole('button', {name: 'Advanced search'}));
  await waitFor(() => expect(screen.getByLabelText('Match name').matches(':disabled')).toBe(false));
  view.unmount();
  render(<ReferenceCollection kind="dispatch_location" refresh={0} currentId={null} open={() => {}}/>);
  await screen.findByText('Search is not available for Dispatch Locations.');
  expect(screen.getByRole('textbox', {name: 'Search Dispatch Locations'}).matches(':disabled')).toBe(true);
});

test('selection, opened identity and arrow focus preserve the clean record name', () => {
  const rows = [{id, label: 'Customer', cells: ['Customer', 1], eligible: true, route: {type: 'customer_organization', id}}, {id: 'other', label: 'Other', cells: ['Other', 1], eligible: true, route: {type: 'customer_organization', id: 'other'}}];
  function Fixture() {const [selection, change] = useState(emptySelection); return <SelectableCollection rows={rows} columns={['Name', 'Revision']} currentId={id} selection={selection} change={change} open={() => {}}/>;}
  render(<Fixture/>);
  const row = screen.getByRole('button', {name: 'Open Customer'}).closest('[role=row]')!;
  fireEvent.click(row);
  expect(row.querySelector('[data-record-name]')?.textContent).toBe('Customer');
  expect(row.querySelector('.collection-row-state')?.textContent).toBe('SelectedOpened');
  fireEvent.keyDown(row, {key: 'ArrowDown'});
  expect(row.getAttribute('aria-selected')).toBe('true');
  expect(row.getAttribute('aria-current')).toBe('true');
  expect(screen.getByRole('button', {name: 'Open Other'}).closest('[role=row]')).toBe(document.activeElement);
});

test('oversized UTF-8 intent remains intact and is rejected before sending a command', async () => {
  function Fixture() {const [value, set] = useState(''); return <Field label="Name" value={value} change={set} maximum={4}/>;}
  render(<Fixture/>);
  fireEvent.change(screen.getByLabelText('Name'), {target: {value: 'ééé'}});
  expect((screen.getByLabelText('Name') as HTMLInputElement).value).toBe('ééé');
  expect(screen.getByText(/6 UTF-8 bytes exceeds the 4-byte/)).toBeTruthy();
  const client = new ApiClient(); client.runId = id;
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
  await expect(client.request('/api/v1/reference/customer-organizations', 'urn:soma:01:mutation-result:v1', {method: 'POST', requestContract: 'urn:soma:01:create-customer-request:v1', body: {command_id: id, name: 'x'.repeat(1025)}})).rejects.toBeInstanceOf(ApiInputError);
  expect(fetch).not.toHaveBeenCalled();
});

test('a revision change retains safe input and requires explicit review before saving', async () => {
  vi.spyOn(api, 'request').mockRejectedValue(notFound());
  function Fixture({revision}: {revision: number}) {
    const root = useRef<HTMLDivElement>(null);
    const working = useWorkingIntent({name: revision === 1 ? 'Original' : 'Concurrent'}, {contract_id: 'reference.edit.customer_organization', contract_version: 1, target_type: 'customer_organization', target_id: id, scope_key: 'metadata', base_revision: String(revision)}, root);
    return <div ref={root}><Field label="Name" value={working.draft.name} change={v => working.edit('name', v)}/><button disabled={working.conflict}>Save</button>{working.recovery}</div>;
  }
  const view = render(<Fixture revision={1}/>);
  fireEvent.change(screen.getByLabelText('Name'), {target: {value: 'Retained intent'}});
  view.rerender(<Fixture revision={2}/>);
  await screen.findByText(/Working intent is stale/);
  expect((screen.getByLabelText('Name') as HTMLInputElement).value).toBe('Retained intent');
  expect((screen.getByRole('button', {name: 'Save'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', {name: 'Use reviewed intent against current revision'}));
  await waitFor(() => expect((screen.getByRole('button', {name: 'Save'}) as HTMLButtonElement).disabled).toBe(false));
  expect((screen.getByLabelText('Name') as HTMLInputElement).value).toBe('Retained intent');
});

test('an uncertain response retries the captured command and body after owner context changes', async () => {
  const send = vi.fn().mockRejectedValueOnce(new Error('Response lost')).mockResolvedValue({outcome: 'APPLIED'});
  const done = vi.fn();
  function Fixture() {const [revision, set] = useState(1), action = useOwnerAction(); return <><button onClick={() => {void action.run(String(revision), command => send({command_id: command, base_revision: revision}), done);}}>Save</button><button onClick={() => set(2)}>New evidence</button>{action.feedback}</>;}
  render(<Fixture/>);
  fireEvent.click(screen.getByRole('button', {name: 'Save'}));
  await screen.findByRole('button', {name: 'Retry exact pending operation'});
  fireEvent.click(screen.getByRole('button', {name: 'New evidence'}));
  fireEvent.click(screen.getByRole('button', {name: 'Retry exact pending operation'}));
  await waitFor(() => expect(done).toHaveBeenCalledTimes(1));
  expect(send.mock.calls[1]?.[0]).toEqual(send.mock.calls[0]?.[0]);
  expect(send.mock.calls[1]?.[0].base_revision).toBe(1);
});

test('invalid recovered appearance text cannot crash rendering or become a silent choice', () => {
  const change = vi.fn(); render(<AppearancePreference valueJson="{partial" change={change} disabled={false}/>);
  expect(screen.getByRole('alert').textContent).toContain('explicit valid choice');
  expect(change).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Appearance preference'), {target: {value: 'core_dark'}});
  expect(change).toHaveBeenCalledWith('"core_dark"');
});

test('blocked or unavailable dependency evidence never enables archive', async () => {
  const preview = {target_type: 'customer_organization', target_id: id, operation: 'archive', revision: 1, exact_blocker_count: 51, blockers: [{validator_id: 'synthetic.owner', blocker_id: id, reason_code: 'LINKED_RECORD'}], continuation: 'bounded-cursor', would_be_eligible: false};
  const request = vi.spyOn(api, 'request').mockImplementation(async path => {
    if (path.endsWith('/archive-preview')) return preview as never;
    throw notFound();
  });
  function Fixture() {const root = useRef<HTMLDivElement>(null); return <div ref={root}><Lifecycle kind="customer_organization" detail={{reference_id: id, reference_type: 'customer_organization', name: 'Customer', name_match_key: 'customer', lifecycle_state: 'active', revision: 1, created_at_utc: 0, updated_at_utc: 0, current_account_code: null}} application={root} refresh={() => {}}/></div>;}
  render(<Fixture/>);
  fireEvent.change(screen.getByLabelText('Lifecycle reason category'), {target: {value: 'operator'}});
  fireEvent.click(screen.getByRole('button', {name: 'Preview archive dependencies'}));
  await screen.findByText('Exact blocker count: 51 · Blocked or indeterminate');
  expect((screen.getByRole('button', {name: 'Archive reference…'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button', {name: 'Next blocker page'}));
  await waitFor(() => expect(request.mock.calls.filter(call => call[0].endsWith('/archive-preview'))).toHaveLength(2));
  request.mockImplementation(async () => {throw new ApiError({code: 'DEPENDENCY_VALIDATION_FAILED', summary: 'Dependency validation is unavailable.', recoverability: 'retry', safe_next_action: null, correlation_id: id});});
  fireEvent.click(screen.getByRole('button', {name: 'Preview archive dependencies'}));
  await screen.findByText('Dependency validation is unavailable.');
  expect((screen.getByRole('button', {name: 'Archive reference…'}) as HTMLButtonElement).disabled).toBe(true);
});
test('clearing a search restores the ordinary cursor instead of restarting its first page', async () => {
  const first={reference_id:id,name:'First',lifecycle_state:'active',revision:1};
  const second={...first,reference_id:'other',name:'Second'};
  const request=vi.spyOn(api,'request').mockImplementation(async path => (path.endsWith('/identities') ? {items: []} : path.includes('/match/') ? {candidate_ids: [],state:'UNRESOLVED',candidate_count:0,explanation:'NO_CANONICAL_CANDIDATE',continuation:null} : {items:[path.includes('after=more') ? second : first],exact_count:2,continuation:path.includes('limit=1') || path.includes('after=more') ? null : 'more',as_of_utc_s:0}) as never);
  render(<ReferenceCollection kind="customer_organization" refresh={0} currentId={null} open={()=>{}}/>);
  await screen.findByRole('button',{name:'Open First'});
  fireEvent.click(screen.getByRole('button',{name:'Next page'}));
  await screen.findByRole('button',{name:'Open Second'});
  fireEvent.change(screen.getByRole('textbox',{name:'Search Customers'}),{target:{value:'Missing'}});
  fireEvent.click(screen.getByRole('button',{name:'Search'}));
  await screen.findByText('No exact candidates');
  fireEvent.click(screen.getByRole('button',{name:'Clear search'}));
  await screen.findByRole('button',{name:'Open Second'});
  await waitFor(()=>expect(request.mock.calls.filter(call=>call[0].includes('after=more'))).toHaveLength(2));
  expect(screen.queryByRole('button',{name:'Open First'})).toBeNull();
});
