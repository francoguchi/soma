import {createRoot} from 'react-dom/client';
import {useEffect, useRef, useState, type FormEvent} from 'react';
import {api, QueryController} from '../shared/api/client';
import type {AuthResultV1, BootstrapV1} from '../shared/api/generated/contracts';
import {buildIdentity} from '../shared/build/identity';
import {applyAppearance} from '../shared/appearance';
import {ErrorState} from '../shared/components/ErrorState';
import {OperatorStatus} from './status/OperatorStatus';
import {useDiagnostics} from '../features/system/useDiagnostics';
import {Diagnostics} from '../features/system/Diagnostics';
import {Navigation, resolveRoute, type ReturnState} from './router';
import {workspaces, systemDestinations, workspaceState} from './workspaces/registry';
import mark from '../assets/brand/soma-mark.svg';
import '../styles/soma.css';
import {installScrollOwnership} from '../shared/interactions/scroll';

function AuthGate({bootstrap, reload}: {bootstrap: BootstrapV1; reload: () => void}) {
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const setup = bootstrap.auth_state === 'setup_required';
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null);
    try {
      await api.request<AuthResultV1>('/api/v1/auth/' + (setup ? 'setup' : 'login'), 'auth-result', {method: 'POST', requestContract: setup ? 'auth-setup-request' : 'auth-login-request', body: setup ? {run_id: bootstrap.run_id, password, confirmation} : {run_id: bootstrap.run_id, password}});
      setPassword(''); setConfirmation(''); reload();
    } catch (caught) {setPassword(''); setConfirmation(''); setError(caught);}
    finally {setBusy(false);}
  }
  return <main className="auth-surface"><div className="auth-card"><img src={mark} alt="SOMA" className="auth-mark"/><p className="eyebrow">Local operations / private instance</p><h1>{setup ? 'Set up Local Administrator' : 'Sign in to SOMA'}</h1><p>{setup ? 'Create the password for this installation. Use at least 12 characters.' : 'Enter your Local Administrator password.'}</p><form onSubmit={event => {void submit(event);}}><label>Password<input type="password" autoComplete={setup ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} required minLength={setup ? 12 : 1} maxLength={1024} autoFocus/></label>{setup && <label>Confirm password<input type="password" autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} required minLength={12} maxLength={1024}/></label>}<button className="primary" disabled={busy}>{busy ? 'Checking...' : setup ? 'Create password and sign in' : 'Sign in'}</button></form>{error !== null && <ErrorState error={error}/>}<small>Single local administrator · Password recovery is not available in this development build.</small></div></main>;
}

export function Application() {
  const [bootstrap, setBootstrap] = useState<BootstrapV1 | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [revision, setRevision] = useState(0);
  const diagnostics = useDiagnostics(bootstrap?.auth_state === 'authenticated' ? bootstrap.run_id : null);
  const [actionError, setActionError] = useState<unknown>(null);
  const [path, setPath] = useState(location.pathname);
  const main = useRef<HTMLElement>(null);
  const context = useRef<ReturnState | null>(null);
  const navigation = useRef(new Navigation(() => context.current));
  useEffect(() => {applyAppearance();}, []);
  useEffect(() => installScrollOwnership(document.documentElement, () => main.current?.querySelector<HTMLElement>('[data-pane-active=true]:not([hidden])') ?? main.current), [bootstrap?.auth_state]);
  useEffect(() => {
    const query = new QueryController<BootstrapV1>();
    void query.query(signal => api.request('/api/v1/bootstrap', 'bootstrap', {signal}), value => {
      try {
        if (!Object.entries(buildIdentity).every(([key, expected]) => value.build[key as keyof typeof value.build] === expected)) throw new Error('Main and Core builds differ. Rebuild and reload SOMA.');
        api.acceptBootstrap(value); setBootstrap(value);
      } catch (caught) {setError(caught);}
    }, setError);
    return () => query.cancel();
  }, [revision]);
  useEffect(() => {
    const pop = (event: PopStateEvent) => {setPath(location.pathname); context.current = (event.state as {context?: ReturnState} | null)?.context ?? null;};
    addEventListener('popstate', pop); return () => removeEventListener('popstate', pop);
  }, []);
  useEffect(() => {if (main.current) {main.current.scrollTop = context.current?.scrollTop ?? 0; main.current.focus();}}, [path, bootstrap?.auth_state]);
  const reload = () => {setError(null); setRevision(value => value + 1);};
  if (error !== null) return <main className="auth-surface"><ErrorState error={error} retry={() => location.reload()}/></main>;
  if (!bootstrap) return <main className="auth-surface"><p role="status">Connecting to local SOMA...</p></main>;
  if (bootstrap.auth_state !== 'authenticated') return <AuthGate bootstrap={bootstrap} reload={reload}/>;
  const route = resolveRoute(path);
  const available = route && workspaceState(route.capability, bootstrap.capabilities) !== 'unavailable';
  async function logout() {
    try {await api.request('/api/v1/auth/logout', 'auth-result', {method: 'POST', body: {}, requestContract: 'empty-request'}); api.csrf = null; reload();} catch (caught) {setError(caught);}
  }
  return <div className="soma-shell"><a className="skip-link" href="#main-content">Skip to content</a><header className="shell-header"><div className="brand"><img src={mark} alt=""/><strong>SOMA</strong><span>LOCAL OPERATIONS</span></div><div className="shell-session"><span>Local Administrator</span><button onClick={() => {void logout();}}>Sign out</button></div></header><nav aria-label="Navigation" className="workspace-nav" data-scroll-owner="both"><div className="product-workspaces" data-scroll-owner="x" tabIndex={0} role="group" aria-label="Workspaces"><p className="eyebrow">Workspaces</p>{workspaces.map(item => {
    const state = workspaceState(item.capability, bootstrap.capabilities);
    return <button key={item.path} disabled={state === 'unavailable'} aria-label={state === 'unavailable' ? item.title + ' - Not available in this build' : item.title + (state === 'development' ? ' - Development' : '')} title={state === 'unavailable' ? 'Not available in this build' : item.title} aria-current={path === item.path ? 'page' : undefined} onClick={() => navigation.current.open(item.path)}><span>{item.title}</span>{state !== 'available' && <small aria-hidden="true">{state === 'development' ? 'dev' : '—'}</small>}</button>;
  })}</div><div className="system-destinations" role="group" aria-label="System"><p className="eyebrow">System</p>{systemDestinations.map(item => <button key={item.path} disabled={workspaceState(item.capability, bootstrap.capabilities) === 'unavailable'} aria-current={path === item.path ? 'page' : undefined} onClick={() => navigation.current.open(item.path)}>{item.title}</button>)}</div><footer>Core Dark<br/>Foundation · {buildIdentity.application_version}</footer></nav><main id="main-content" ref={main} tabIndex={-1} className="main-scroll" data-scroll-owner="y" onScroll={() => {context.current = {filters: {}, activeId: null, selectedIds: [], pane: null, tab: null, scrollTop: main.current?.scrollTop ?? 0, focusToken: 'main-content'};}}>{!available ? <section><h1>{route?.title ?? 'Page not found'}</h1><p>Not available in this build.</p><button onClick={() => navigation.current.open('/system/diagnostics')}>Go to Diagnostics</button></section> : <Diagnostics {...diagnostics} actionError={actionError} setActionError={setActionError}/>}</main><OperatorStatus bootstrap={bootstrap} diagnostics={diagnostics.value} unavailable={diagnostics.error !== null}/></div>;
}
createRoot(document.getElementById('root')!).render(<Application/>);
