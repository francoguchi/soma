import {useRef, useState} from 'react';
import {afterEach, expect, test, vi} from 'vitest';
import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {api, ApiError, ApiInputError, ApiClient} from '../shared/api/client';
import {resolveRoute} from '../app/router';
import {Candidates} from '../features/reference/components/Candidates';
import {Field, useOwnerAction} from '../features/reference/model';
import {useWorkingIntent} from '../shared/interactions/use-working-intent';
import {AppearancePreference} from '../shared/appearance-preference';
import {Lifecycle} from '../features/reference/components/Lifecycle';

afterEach(() => {cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals();});
const id = '4d204e28-3a66-43cb-81ca-a31cc94c9b11';
const notFound = () => new ApiError({code: 'WORKING_COPY_NOT_FOUND', summary: 'No copy.', recoverability: 'none', safe_next_action: null, correlation_id: id});

test('contextual reference routes remain under Settings and reject unknown or injected paths', () => {
  expect(resolveRoute('/settings/reference-data/contact/' + id)?.capability).toBe('settings');
  expect(resolveRoute('/settings/reference-data/dispatch_location/new')?.title).toBe('Settings');
  for (const path of ['/customers', '/settings/reference-data/contacts', '/settings/reference-data/contact/invalid', '/settings/reference-data/contact/' + id + '/delete']) expect(resolveRoute(path)).toBeNull();
});

test('an exact unique candidate is evidence and opens only after explicit activation', async () => {
  vi.spyOn(api, 'request').mockImplementation(async path => (path.endsWith('/identities') ? {items: [{reference_id: id, name: 'Customer', lifecycle_state: 'active', revision: 1}]} : {candidate_ids: [id], state: 'UNIQUE_CANDIDATE', candidate_count: 1, explanation: 'ACCOUNT_CODE_MATCH', continuation: null}) as never);
  const open = vi.fn();
  render(<Candidates kind="customer_organization" open={open}/>);
  fireEvent.change(screen.getByLabelText('Match Account Code'), {target: {value: 'CODE'}});
  fireEvent.click(screen.getByRole('button', {name: 'Find candidates'}));
  await screen.findByText('UNIQUE_CANDIDATE · 1 exact candidates');
  expect(open).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('row'));
  expect(open).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', {name: 'Open Customer · revision 1'}));
  expect(open).toHaveBeenCalledExactlyOnceWith(id);
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
