import type {ReactNode, RefObject} from 'react';
import type {BootstrapV1} from '../../shared/api/generated/contracts';
import {SomaIcon, type IconName} from '../../shared/components/SomaIcon';
import {workspaces, workspaceState} from './registry';

const icons: Record<string, IconName> = {overview: 'overview', tickets: 'tickets', objectives: 'objectives', inventory: 'inventory', infrastructure: 'infrastructure'};
/** Registered navigation; contextual content and factual status remain caller owned. */
export function OperationalFrame({application, path, capabilities, navigate, settings, context, children, status, caption}: {
  application: RefObject<HTMLDivElement | null>; path: string; capabilities: BootstrapV1['capabilities']; navigate: (path: string) => void;
  settings: () => void; context: ReactNode; children: ReactNode; status: ReactNode; caption?: string;
}) {
  return <div ref={application} className="operational-frame"><header className="operational-topbar"><strong>SOMA</strong>{caption && <span>{caption}</span>}
    <button aria-label="Settings" title="Settings" onClick={settings}><SomaIcon name="settings"/></button></header>
    <nav className="operational-dock" aria-label="Workspaces">{workspaces.filter(item => item.capability !== 'settings').map(item => {
      const state = workspaceState(item.capability, capabilities), disabled = state === 'unavailable';
      return <button key={item.path} aria-label={item.title} title={item.title + (disabled ? ' — Not available in this build' : '')}
        aria-current={path === item.path ? 'page' : undefined} disabled={disabled} onClick={() => navigate(item.path)}><SomaIcon name={icons[item.capability]!}/></button>;
    })}</nav><nav className="operational-context-nav" aria-label="Workspace navigation">{context}</nav>
    <main className="operational-main">{children}</main><div className="operational-footer"><span className="command-reservation" aria-label="Future command area reserved"/>{status}</div>
  </div>;
}
