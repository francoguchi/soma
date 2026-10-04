// Synthetic owners live only in this test fixture, outside the application bundle.
import {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {api} from '../shared/api/client';
import type {BootstrapV1, WorkingCopyKeyV1} from '../shared/api/generated/contracts';
import {discardRecovery, holdProviders, proofBinding, recoveryTransport, restoreRecovery} from '../shared/api/recovery';
import {emptySelection, type Selection} from '../shared/interactions/selection';
import {WorkingCopyClient} from '../shared/interactions/working-copy';
import {installScrollOwnership} from '../shared/interactions/scroll';
import {SafeUndo, type SafeInverse} from '../shared/interactions/undo';
import {Autocomplete, type OptionsPage} from '../shared/components/Autocomplete';
import {HoldButton} from '../shared/components/HoldButton';
import {Confirmation} from '../shared/components/Confirmation';
import {Modal} from '../shared/components/Modal';
import {Workbench} from '../shared/components/Workbench';
import {UndoOpportunity} from '../shared/components/UndoOpportunity';
import {SelectableCollection} from '../shared/collections/SelectableCollection';
import {BoundedCollection, type Page} from '../shared/collections/BoundedCollection';
import '../styles/soma.css';
import './interactions.css';

const rows=Array.from({length:240},(_,i)=>({id:'probe-'+i,label:'Record '+i,eligible:i!==2,route:{type:'probe',id:'probe-'+i}}));
const key:WorkingCopyKeyV1={contract_id:'ProbeEditV1',contract_version:1,target_type:'probe',target_id:'probe-a',scope_key:'notes',base_revision:'rev-1'};
const baseBinding={action_code:'probe.hold',target_type:'probe',target_id:'probe-a',base_revision:'rev-1',preview_fingerprint:null,route:'/probe'};
function Fixture() {
  const root=useRef<HTMLElement>(null), primary=useRef<HTMLElement>(null);
  const [ready,setReady]=useState(false), [selection,setSelection]=useState<Selection>(emptySelection()),[opened,setOpened]=useState('none'),[filter,setFilter]=useState(''),[modal,setModal]=useState(false),[accepted,setAccepted]=useState(0),[target,setTarget]=useState('probe-a'),[commands,setCommands]=useState(0),[choice,setChoice]=useState('none'),[note,setNote]=useState(''),[recovery,setRecovery]=useState('memory_only'),[recoveryInfo,setRecoveryInfo]=useState('none'),[undoCount,setUndoCount]=useState(0),[restoreState,setRestoreState]=useState('none');
  const copy=useMemo(()=>new WorkingCopyClient(recoveryTransport<{note:string}>(api,key),()=>setRecovery(copy.status)),[]);
  const holds=useMemo(()=>holdProviders(api,async(binding,proof)=>{const result=await api.request('/api/v1/probe/accept','empty-request',{method:'POST',requestContract:'proof-authorization',body:{binding:proofBinding(binding),proof_token:proof.proof_token}});setCommands(value=>value+1);return result;}),[]);
  const search=useMemo(()=>async(query:string,cursor:string|null,limit:number,signal:AbortSignal):Promise<OptionsPage>=>{
    await new Promise(resolve=>setTimeout(resolve,query==='slow'?500:30)); if(signal.aborted)throw new DOMException('Aborted','AbortError');
    if(query==='error')throw new Error('Synthetic owner unavailable'); if(query==='none')return{items:[],continuation:null,partial:false,warnings:[]};
    const offset=cursor===null?0:25;return{items:Array.from({length:limit},(_,i)=>({id:query+'-'+(offset+i),label:query+' option '+(offset+i),eligible:i!==1})),continuation:offset===0?'opaque-next':null,partial:offset===0,warnings:['Synthetic source warning']};
  },[]);
  const load=useMemo(()=>async(cursor:string|null,limit:number,signal:AbortSignal):Promise<Page<typeof rows[number]>>=>{await new Promise(resolve=>setTimeout(resolve,20));if(signal.aborted)throw new DOMException('Aborted','AbortError');const offset=cursor===null?0:100; return{items:rows.filter(row=>row.label.includes(filter)).slice(offset,offset+limit),continuation:offset===0?'opaque-next':null,as_of_utc_s:1000,partial:offset===0,total:240,warnings:['Owner page warning']};},[filter]);
  const undo=useMemo(()=>{const inverse:SafeInverse={commandContract:'ProbeInverseV1',preview:async()=>({state:'AVAILABLE',fingerprint:'a'.repeat(64),reason:null,consequence:'Restore this owner action only.',blockers:[]}),build:async op=>({target:op.target,postRevision:op.postRevision}),submit:async()=>{setUndoCount(value=>value+1);return{};}}; const store=new SafeUndo(new Map([['probe:edit',inverse]])); for(const id of ['one','two'])store.remember({id,owner:'probe',inverseKind:'edit',actionResultRef:'result:'+id,target:{type:'probe',id},postRevision:'rev-1'});return store;},[]);
  useEffect(()=>{const run=async()=>{let boot=await api.request<BootstrapV1>('/api/v1/bootstrap','bootstrap');api.acceptBootstrap(boot);if(boot.auth_state==='setup_required'){await api.request('/api/v1/auth/setup','auth-result',{method:'POST',requestContract:'auth-setup-request',body:{run_id:api.runId,password:'Synthetic interaction password 42',confirmation:'Synthetic interaction password 42'}});boot=await api.request('/api/v1/bootstrap','bootstrap');api.acceptBootstrap(boot);}setReady(true);};void run(); const remove=installScrollOwnership(document.documentElement,()=>primary.current);return()=>{remove();copy.dispose();};},[]);
  const recover=async()=>{try{const value=await restoreRecovery(api,key);setRecoveryInfo('Generation '+value.generation);setRestoreState(value.conflict?'conflict':'current');}catch{setRestoreState('unavailable');}};
  return <main ref={root} className="fixture" id="application"><h1 tabIndex={-1}>Foundation interaction fixture</h1><p role="status">{ready?'Authenticated fixture ready':'Preparing real host session'}</p><p>Selected {selection.selected_id??'none'} · Active {selection.active_id??'none'} · Opened {opened}</p><p>Owner commands: <output id="commands">{commands}</output> · Modal accepted: <output id="accepted">{accepted}</output> · Undo commands: <output id="undo-count">{undoCount}</output></p>
    <label>Filter <input aria-label="Filter" value={filter} onChange={event=>setFilter(event.target.value)}/></label>
    <Workbench dirty={copy.hasUnsavedIntent()} work={<><h2>Operational work</h2><label>Working note <input aria-label="Working note" value={note} onChange={event=>{setNote(event.target.value);copy.edit({draft:{note:event.target.value},dirty_paths:['/note']});}}/></label><p id="recovery">Recovery: {recovery}</p><button onClick={()=>{void recover();}}>Inspect recovery</button><p id="recovery-info">{recoveryInfo} · Restore {restoreState}</p><button onClick={()=>{void restoreRecovery(api,key).then(value=>discardRecovery(api,value.working_copy_id,value.generation,crypto.randomUUID())).then(()=>setRestoreState('discarded'));}}>Discard recovery</button>
      <BoundedCollection queryKey={filter} load={load} render={(page,stale)=><SelectableCollection rows={page.items.map(row=>({...row,eligible:row.eligible&&!stale}))} selection={selection} change={setSelection} open={row=>setOpened(row.id)} multi/>}/></>} context={<><h2>Context and evidence</h2><label>Evidence filter <input aria-label="Evidence filter" defaultValue="Keep context"/></label><Autocomplete label="Find existing record" search={search} choose={option=>setChoice(option.id)}/><p id="choice">Chosen {choice}</p><button id="invoke" onClick={()=>setModal(true)}>Open long modal</button>
      <HoldButton key={target} label="Confirm synthetic owner action" binding={{...baseBinding,target_id:target}} available={ready} providers={holds}/><button onClick={()=>setTarget(value=>value==='probe-a'?'probe-b':'probe-a')}>Change target</button><p id="target">Target {target}</p>
      <Confirmation tier="preview_plus_hold" label="Preview synthetic action" binding={{...baseBinding,action_code:'probe.preview',preview_fingerprint:'a'.repeat(64)}} available={ready} providers={holds} activate={async()=>({})} application={root} fallback={()=>document.querySelector('h1')} preview={{binding:{...baseBinding,action_code:'probe.preview',preview_fingerprint:'a'.repeat(64)},current:true,targets:['probe-a'],effects:['Record this synthetic owner command only.'],blockers:[]}}/>
      <UndoOpportunity id="one" undo={undo}/><UndoOpportunity id="two" undo={undo}/></>}/>
    <section ref={primary} id="outer" data-scroll-owner="both" tabIndex={0}><h2>Outer owner</h2><div id="inner" data-scroll-owner="both" tabIndex={0}><div className="overflow-content">Inner scroll owner</div></div><div className="overflow-content">Outer overflow</div></section><section id="sibling" data-scroll-owner="both" tabIndex={0}><div className="overflow-content">Sibling owner</div></section>
    {modal&&<Modal title="Long consequential modal" application={root} fallback={()=>document.querySelector('h1')} close={()=>setModal(false)}>{isolated=><><button disabled={!isolated} onClick={()=>{setAccepted(value=>value+1);setModal(false);}}>Accept consequence</button><div className="long-evidence">{Array.from({length:35},(_,i)=><p key={i}>Synthetic material effect {i}. Review before continuing.</p>)}</div></>}</Modal>}
  </main>;
}
createRoot(document.getElementById('fixture-root')!).render(<Fixture/>);
