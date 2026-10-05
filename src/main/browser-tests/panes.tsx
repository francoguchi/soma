// Development-only three-pane interaction owner; excluded from the Main bundle.
import {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {ConsolePanes} from '../shared/components/ConsolePanes';
import {SelectableCollection} from '../shared/collections/SelectableCollection';
import {Modal} from '../shared/components/Modal';
import {emptySelection} from '../shared/interactions/selection';
import {installScrollOwnership} from '../shared/interactions/scroll';
import {api} from '../shared/api/client';
import type {BootstrapV1} from '../shared/api/generated/contracts';
import {useDiagnostics} from '../features/system/useDiagnostics';
import {OperatorStatus} from '../app/status/OperatorStatus';
import '../styles/soma.css';
import './panes.css';

function Fixture() {
  const root = useRef<HTMLDivElement>(null), main = useRef<HTMLElement>(null);
  const [selection, setSelection] = useState(emptySelection()), [opened, setOpened] = useState('none');
  const [modal, setModal] = useState(false), [bootstrap, setBootstrap] = useState<BootstrapV1 | null>(null);
  const diagnostics = useDiagnostics(bootstrap?.run_id ?? null);
  useEffect(() => {
    void api.request<BootstrapV1>('/api/v1/bootstrap', 'bootstrap').then(value => {api.acceptBootstrap(value); setBootstrap(value);});
    return installScrollOwnership(document.documentElement, () => main.current?.querySelector<HTMLElement>('[data-pane-active=true]:not([hidden]) [data-pane-body]') ?? main.current);
  }, []);
  return <div ref={root} className="soma-shell pane-fixture"><header className="shell-header"><strong>SOMA / Pane focus fixture</strong></header><main ref={main} className="main-scroll"><section className="diagnostics-surface"><header className="surface-header"><div><h1 tabIndex={-1}>Synthetic pane inspection</h1><p id="pane-selection">Selected {selection.selected_id ?? 'none'} / Opened {opened}</p></div></header><ConsolePanes panes={[
    {id: 'list', title: 'Operational list', content: <><label>Pane filter <input defaultValue="Preserve filter"/></label><SelectableCollection rows={Array.from({length: 20}, (_, i) => ({id: 'pane-' + i, label: 'Pane record ' + i, eligible: true, route: {type: 'probe', id: 'pane-' + i}}))} selection={selection} change={setSelection} open={row => setOpened(row.id)}/></>},
    {id: 'evidence', title: 'Evidence', content: <><label>Pane working note <input defaultValue="Preserve dirty intent"/></label><button onClick={() => setModal(true)}>Inspect pane modal</button><p>Owner warnings stay visible with their evidence.</p></>},
    {id: 'activity', title: 'Activity', content: <ol>{Array.from({length: 50}, (_, i) => <li key={i}>Synthetic activity {i}</li>)}</ol>},
  ]}/></section></main>{bootstrap && <OperatorStatus bootstrap={bootstrap} diagnostics={diagnostics.value} unavailable={diagnostics.error !== null}/>} {modal && <Modal title="Pane inspection modal" application={root} fallback={() => main.current?.querySelector('h1') ?? null} close={() => setModal(false)}>{() => <p>Inspection does not select or accept a record.</p>}</Modal>}</div>;
}
createRoot(document.getElementById('pane-root')!).render(<Fixture/>);
