import {afterEach, expect, test, vi} from 'vitest';
import {act, cleanup, fireEvent, render, screen} from '@testing-library/react';
import {createRef} from 'react';
import {DeliberateHold, type HoldBinding, type HoldProviders} from '../shared/interactions/hold';
import {WorkingCopyClient} from '../shared/interactions/working-copy';
import {emptySelection, restoreSelection, selectionOpen, type Row} from '../shared/interactions/selection';
import {SafeUndo, type SafeInverse, type Opportunity} from '../shared/interactions/undo';
import {NavigationGuard, warnBeforeUnload} from '../shared/interactions/navigation-guard';
import {draftJson} from '../shared/api/recovery';
import {SelectableCollection} from '../shared/collections/SelectableCollection';
import {BoundedCollection, type Page} from '../shared/collections/BoundedCollection';
import {Autocomplete} from '../shared/components/Autocomplete';
import {Modal} from '../shared/components/Modal';
import {Confirmation} from '../shared/components/Confirmation';
import {HoldButton} from '../shared/components/HoldButton';

afterEach(() => {cleanup(); vi.useRealTimers(); vi.restoreAllMocks();});
const uuid = '12345678-1234-4234-8234-123456789abc', hash = 'a'.repeat(64);
const binding: HoldBinding = {action_code:'probe.hold', target_type:'probe', target_id:'a', base_revision:'rev-1', preview_fingerprint:null, route:'/probe'};
const challenge = {challenge_id: uuid, expires_in_ms:15000 as const};
const proof = {proof_token:'p'.repeat(44), expires_in_ms:30000 as const};
function providers(): HoldProviders {return {issue:vi.fn(async () => challenge), complete:vi.fn(async () => proof), submit:vi.fn(async () => ({})), abandon:vi.fn()};}
const row = (id: string, eligible = true): Row & {label: string} => ({id, eligible, route:{type:'probe',id}, label:id});

test('click selects, arrows only move active, Space marks members and Open requires explicit eligible body', () => {
  let selection = selectionOpen(emptySelection(), {kind:'click',row:row('a'),nestedControl:false});
  expect(selection.selected_id).toBe('a'); expect(selection.opened_ref).toBeNull();
  selection = selectionOpen(selection,{kind:'arrow',row:row('b'),selectionFollowsFocus:false});
  expect(selection.active_id).toBe('b'); expect(selection.selected_id).toBe('a');
  selection = selectionOpen(selection,{kind:'space',row:row('b'),multi:true}); expect(selection.member_ids).toEqual(['b']);
  expect(selectionOpen(selection,{kind:'open',row:row('b'),nestedControl:true})).toBe(selection);
  expect(selectionOpen(selection,{kind:'open',row:row('c',false),nestedControl:false})).toBe(selection);
  expect(selectionOpen(selection,{kind:'open',row:row('b'),nestedControl:false}).opened_ref).toEqual({type:'probe',id:'b'});
});
test('removed row restores nearest eligible survivor with explicit explanation', () => {
  const result = restoreSelection({...emptySelection(),active_id:'b',selected_id:'b',member_ids:['b','c']},[row('a'),row('c')],['a','b','c']);
  expect(result.selection.active_id).toBe('a'); expect(result.selection.member_ids).toEqual(['c']); expect(result.explanation).toContain('unavailable');
});
test('nested checkbox and Open button never fall through to body selection', () => {
  const change=vi.fn(), open=vi.fn(); render(<SelectableCollection rows={[row('a'),row('b',false)]} selection={emptySelection()} change={change} open={open} multi/>);
  fireEvent.click(screen.getByLabelText('Select a')); expect(open).not.toHaveBeenCalled(); expect(change).toHaveBeenCalledOnce();
  change.mockClear(); fireEvent.click(screen.getByRole('button',{name:'Open a'})); expect(open).toHaveBeenCalledOnce(); expect(change.mock.calls[0]?.[0].selected_id).toBeNull();
  fireEvent.doubleClick(screen.getByText('b')); expect(open).toHaveBeenCalledOnce();
});
test('hold cannot finish at 2999ms and claims proof and dispatch exactly once', async () => {
  let now=0; const owner=providers(), hold=new DeliberateHold(owner,()=>now); await hold.start(binding,true);
  now=2999; expect(await hold.finish(binding)).toBeNull(); expect(owner.complete).not.toHaveBeenCalled();
  now=3000; await Promise.all([hold.finish(binding),hold.finish(binding)]);
  expect(owner.complete).toHaveBeenCalledOnce(); expect(owner.submit).toHaveBeenCalledOnce();
});
test.each(['action_code','target_id','target_type','base_revision','route','preview_fingerprint'] as const)('changing %s abandons hold without owner dispatch', async key => {
  let now=0; const owner=providers(),hold=new DeliberateHold(owner,()=>now); await hold.start(binding,true); now=3000;
  expect(await hold.finish({...binding,[key]:'changed'})).toBeNull(); expect(owner.submit).not.toHaveBeenCalled(); expect(owner.abandon).toHaveBeenCalledOnce();
});
test('release during proof completion suppresses late response; expiry suppresses proof', async () => {
  let now=0, release!: (value:typeof proof)=>void; const owner={...providers(),complete:vi.fn(()=>new Promise<typeof proof>(resolve=>{release=resolve;}))};
  const hold=new DeliberateHold(owner,()=>now); await hold.start(binding,true); now=3000; const done=hold.finish(binding); hold.cancel(); release(proof); await done; expect(owner.submit).not.toHaveBeenCalled();
  await hold.start(binding,true); now=18000; expect(hold.progress(binding)).toBe(0); expect(hold.phase).toBe('cancelled');
});
test('recovery waits 5s idle and 30s between successful checkpoints; checkpoint is never accepted save', async () => {
  vi.useFakeTimers(); const transport=vi.fn(async (_draft:unknown,generation:number)=>({workingCopyId:uuid,generation:generation+1,contentHash:hash}));
  const client=new WorkingCopyClient(transport,()=>{},()=>Date.now()); client.edit({note:'first'});
  await vi.advanceTimersByTimeAsync(4999); expect(transport).not.toHaveBeenCalled(); await vi.advanceTimersByTimeAsync(1); expect(client.status).toBe('checkpointed'); expect(client.hasUnsavedIntent()).toBe(true);
  client.edit({note:'second'}); await vi.advanceTimersByTimeAsync(29999); expect(transport).toHaveBeenCalledOnce(); await vi.advanceTimersByTimeAsync(1); expect(transport).toHaveBeenCalledTimes(2);
  client.acceptedSave(); expect(client.hasUnsavedIntent()).toBe(false); client.dispose();
});
test('lost checkpoint response retries exact command and intent before newer edits', async () => {
  vi.useFakeTimers(); const transport=vi.fn().mockRejectedValueOnce(new Error('lost response')).mockResolvedValue({workingCopyId:uuid,generation:1,contentHash:hash});
  const client=new WorkingCopyClient(transport,()=>{},()=>Date.now()); client.edit({note:'original'}); await vi.advanceTimersByTimeAsync(5000); expect(client.status).toBe('error');
  client.edit({note:'newer'}); await vi.advanceTimersByTimeAsync(5000);
  expect(transport.mock.calls[1]?.slice(0,3)).toEqual(transport.mock.calls[0]?.slice(0,3)); expect(client.memory()).toEqual({note:'newer'}); expect(client.status).toBe('memory_only'); client.dispose();
});
test('stale restore and generation conflict preserve input and require owner resolution', async () => {
  vi.useFakeTimers(); const transport=vi.fn(async()=>{throw new Error('WORKING_COPY_GENERATION_CONFLICT');}); const client=new WorkingCopyClient(transport,()=>{},()=>Date.now());
  client.edit({note:'keep'}); await vi.advanceTimersByTimeAsync(5000); expect(client.status).toBe('conflict'); expect(client.memory()).toEqual({note:'keep'}); client.edit({note:'still keep'}); await vi.advanceTimersByTimeAsync(40000); expect(transport).toHaveBeenCalledOnce(); client.dispose();
  const recovered=new WorkingCopyClient(transport,()=>{}); recovered.restore({note:'old'},{workingCopyId:uuid,generation:2,contentHash:hash},'STALE'); expect(recovered.status).toBe('conflict'); expect(()=>recovered.restore({note:'replace'},{workingCopyId:uuid,generation:2,contentHash:hash},'CURRENT')).toThrow('clean'); recovered.dispose();
});
test.each([undefined,NaN,Infinity,new Date(),{omitted:undefined},[,,],{bad:'\ud800'}])('recovery rejects lossy non-JSON input %#', value=>{expect(()=>draftJson(value)).toThrow();});
test('recovery serializes finite JSON without silently accepting cyclic or overlong text',()=>{expect(JSON.parse(draftJson({value:1e-7,negative:-0}))).toEqual({value:1e-7,negative:0}); const cycle:unknown[]=[]; cycle.push(cycle); expect(()=>draftJson(cycle)).toThrow(); expect(()=>draftJson({note:'é'.repeat(131073)})).toThrow('byte');});
test('dirty same-flow navigation preserves intent; other-flow requires explicit abandon',()=>{
  const guard=new NavigationGuard(),navigate=vi.fn(); expect(guard.request('a','a',true,navigate)).toBe(true); expect(guard.request('a','b',true,navigate)).toBe(false); guard.stay(); guard.abandon(); expect(navigate).toHaveBeenCalledOnce(); guard.request('a','b',true,navigate); guard.abandon(); expect(navigate).toHaveBeenCalledTimes(2);
  const remove=warnBeforeUnload(()=>true),event=new Event('beforeunload',{cancelable:true}); dispatchEvent(event); expect(event.defaultPrevented).toBe(true); remove();
});
const opportunity=(id:string):Opportunity=>({id,owner:'probe',inverseKind:'edit',actionResultRef:'result:'+id,target:{type:'probe',id},postRevision:'rev-1'});
test('Undo retains independent opportunities and rejects changed preview before inverse dispatch',async()=>{
  let fingerprint=hash; const owner:SafeInverse={commandContract:'ProbeInverseV1',preview:vi.fn(async()=>({state:'AVAILABLE' as const,fingerprint,reason:null,consequence:'Restore this owner action only.',blockers:[]})),build:vi.fn(async()=>({})),submit:vi.fn(async()=>({}))};
  const undo=new SafeUndo(new Map([['probe:edit',owner]])); expect(undo.remember(opportunity('a'))).toBe(true); undo.remember(opportunity('b')); fingerprint='b'.repeat(64); expect(await undo.execute('a',hash)).toBe(false); expect(owner.submit).not.toHaveBeenCalled(); expect(await undo.execute('b',fingerprint)).toBe(true); expect(undo.list().map(item=>item.id)).toEqual(['a']);
  expect(undo.remember({...opportunity('c'),owner:'unknown'})).toBe(false); expect((await undo.availability('missing')).reason).toContain('registered');
});
test('Undo capacity is bounded to 20 independent owner-approved opportunities',()=>{const owner:SafeInverse={commandContract:'P',preview:async()=>({state:'BLOCKED',fingerprint:null,reason:'Owner blocker',consequence:null,blockers:['Owner blocker']}),build:async()=>({}),submit:async()=>({})}; const undo=new SafeUndo(new Map([['probe:edit',owner]])); for(let i=0;i<21;i++)undo.remember(opportunity(String(i))); expect(undo.list()).toHaveLength(20); expect(undo.list()[0]?.id).toBe('1');});
test('autocomplete does not enumerate on focus and supersedes old query without entity creation',async()=>{
  vi.useFakeTimers(); let old!: (value:{items:[],continuation:null,partial:false,warnings:[]})=>void;
  const search=vi.fn((query:string)=>query==='ab'?new Promise<{items:[],continuation:null,partial:false,warnings:[]}>(resolve=>{old=resolve;}):Promise.resolve({items:[{id:'new',label:'New record',eligible:true}],continuation:null,partial:false,warnings:[]})), choose=vi.fn();
  render(<Autocomplete label="Find" search={search} choose={choose}/>); const input=screen.getByRole('combobox'); fireEvent.focus(input); expect(search).not.toHaveBeenCalled(); fireEvent.change(input,{target:{value:'a'}}); await act(()=>vi.advanceTimersByTimeAsync(200)); expect(search).not.toHaveBeenCalled();
  fireEvent.change(input,{target:{value:'ab'}}); await act(()=>vi.advanceTimersByTimeAsync(150)); fireEvent.change(input,{target:{value:'abc'}}); await act(()=>vi.advanceTimersByTimeAsync(150)); await act(async()=>{old({items:[],continuation:null,partial:false,warnings:[]});}); expect(screen.getByRole('option').textContent).toBe('New record');
  fireEvent.keyDown(input,{key:'Enter'}); expect(choose).not.toHaveBeenCalled(); fireEvent.keyDown(input,{key:'Escape'}); expect(choose).not.toHaveBeenCalled();
});
test('collection keeps stale page and warnings on owner failure, never renders more than 200',async()=>{
  const page:Page<string>={items:['original'],continuation:'opaque',as_of_utc_s:1000,partial:true,warnings:['Owner warning'],total:null}; const load=vi.fn(async(_cursor:string|null,_limit:number,_signal:AbortSignal)=>page); const view=render(<BoundedCollection<string> queryKey="a" load={load} render={(value,stale)=><button disabled={stale}>{value.items[0]}</button>}/>);
  await screen.findByText('original'); expect(load.mock.calls[0]?.[1]).toBe(100); expect(screen.getByText('Warning: Owner warning')).toBeTruthy();
  const fail=async()=>{throw new Error('owner unavailable');}; view.rerender(<BoundedCollection<string> queryKey="b" load={fail} render={(value,stale)=><button disabled={stale}>{value.items[0]}</button>}/>); await screen.findByRole('alert'); expect((screen.getByText('original') as HTMLButtonElement).disabled).toBe(true); expect((screen.getByRole('button',{name:'Next page'}) as HTMLButtonElement).disabled).toBe(true); expect(screen.getByText('Warning: Owner warning')).toBeTruthy();
  const tooMany=async()=>({...page,items:Array.from({length:201},(_,i)=>String(i))}); view.rerender(<BoundedCollection<string> queryKey="c" load={tooMany} render={value=>value.items.length > 200 ? 'bad page' : 'original'}/>); await screen.findByText('Collection exceeds the page bound. Refresh with a smaller owner query.'); expect(screen.queryByText('bad page')).toBeNull();
});
test('unsupported dialog isolation fails closed; preview cannot replace exact owner binding',async()=>{
  const application=createRef<HTMLElement>(); application.current=document.createElement('main'); document.body.append(application.current); const close=vi.fn(); const view=render(<Modal title="Consequence" application={application} fallback={()=>application.current} close={close}>{()=> <button>Accept</button>}</Modal>);
  expect((screen.getByText('Accept') as HTMLButtonElement).closest('fieldset')?.disabled).toBe(true); fireEvent.keyDown(screen.getByRole('dialog'),{key:'Escape'}); expect(close).toHaveBeenCalledOnce(); view.unmount();
  const activate=vi.fn(async()=>({})); render(<Confirmation tier="hold" label="Protected" binding={binding} available providers={undefined as never} activate={activate} application={application} fallback={()=>application.current}/>); expect(screen.getByText('Confirmation provider unavailable.')).toBeTruthy(); expect(activate).not.toHaveBeenCalled(); application.current.remove();
});

test.each(['Escape','blur','popstate','scroll','visibility','stale'] as const)('hold component cancels %s without late proof or command',async(reason)=>{
  vi.useFakeTimers({toFake:['setTimeout','clearTimeout','requestAnimationFrame','cancelAnimationFrame','performance']});
  const owner=providers(); const view=render(<HoldButton label="Protected" binding={binding} available providers={owner}/>); const button=screen.getByRole('button',{name:'Protected'});
  await act(async()=>{fireEvent.keyDown(button,{key:' '});}); await act(()=>vi.advanceTimersByTimeAsync(200));
  await act(async()=>{if(reason==='Escape')fireEvent.keyDown(button,{key:'Escape'});else if(reason==='blur')dispatchEvent(new Event('blur'));else if(reason==='popstate')dispatchEvent(new Event('popstate'));else if(reason==='scroll')dispatchEvent(new Event('soma-scroll-gesture'));else if(reason==='visibility'){vi.spyOn(document,'hidden','get').mockReturnValue(true);document.dispatchEvent(new Event('visibilitychange'));}else view.rerender(<HoldButton label="Protected" binding={binding} available={false} providers={owner}/>);});
  await act(()=>vi.advanceTimersByTimeAsync(4000)); expect(owner.complete).not.toHaveBeenCalled(); expect(owner.submit).not.toHaveBeenCalled(); expect(owner.abandon).toHaveBeenCalledOnce();
});
test('owner Undo blockers and missing consequence fail closed',async()=>{
  const submit=vi.fn(async()=>({})); const owner:SafeInverse={commandContract:'P',preview:async()=>({state:'AVAILABLE',fingerprint:hash,consequence:'Reverse only this action.',reason:null,blockers:['Owner blocker']}),build:async()=>({}),submit};const store=new SafeUndo(new Map([['probe:edit',owner]]));store.remember(opportunity('one'));expect((await store.availability('one')).state).toBe('BLOCKED');expect(await store.execute('one')).toBe(false);expect(submit).not.toHaveBeenCalled();
  const missing=new SafeUndo(new Map([['probe:edit',{...owner,preview:async()=>({state:'AVAILABLE',fingerprint:hash,consequence:null,reason:null,blockers:[]})}]]));missing.remember(opportunity('one'));expect((await missing.availability('one')).state).toBe('INDETERMINATE');
});
