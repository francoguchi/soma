import type {BootstrapV1, DiagnosticsV1} from '../../shared/api/generated/contracts';

export function OperatorStatus({bootstrap, diagnostics, unavailable = false}: {bootstrap: BootstrapV1; diagnostics: DiagnosticsV1 | null; unavailable?: boolean}) {
  const current = diagnostics?.health.run_id === bootstrap.run_id ? diagnostics : null;
  const health = current?.health;
  const degraded = !!current && (current.partial.length > 0 || !current.logging_available);
  const readiness = unavailable ? 'Unavailable' : !health ? 'Checking' : health.host_state;
  const schema = health ? health.last_migration_id : 'unavailable';
  const protection = health?.integrity_state === 'verified' ? 'loopback / encrypted' : 'protection unavailable';
  const condition = unavailable || degraded || health?.host_state === 'FAILED' ? 'degraded' : health?.host_state === 'READY' ? 'ready' : 'normal';
  const facts = <><span>schema {schema}</span><span>{bootstrap.build.build_kind === 'source' ? 'development' : 'build unavailable'} · {bootstrap.build.application_version}</span><span>{protection}</span>{degraded && <span>Partial: {current?.partial.join(', ') || 'logging unavailable'}</span>}</>;
  return <footer className="shell-status" aria-label="Operator status" data-condition={condition}>
    <span className="status-primary">run {bootstrap.run_id.slice(0, 8)} <span className="status-readiness">{readiness}{degraded && !unavailable ? ' / DEGRADED' : ''}</span></span>
    <div className="status-secondary">{facts}</div>
    <details className="status-details"><summary aria-label="Operator status details">Details</summary><div aria-label="Secondary operator status">{facts}<small>Canonical evidence is available in Diagnostics.</small></div></details>
  </footer>;
}
