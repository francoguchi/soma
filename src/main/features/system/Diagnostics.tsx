import type {DiagnosticsV1} from '../../shared/api/generated/contracts';
import {displayTime} from '../../shared/time';
import {ErrorState} from '../../shared/components/ErrorState';
import {api} from '../../shared/api/client';
import {ConsolePanes} from '../../shared/components/ConsolePanes';
export function Diagnostics({value, error, refresh, actionError, setActionError}: {value: DiagnosticsV1 | null; error: unknown; refresh: () => void; actionError: unknown; setActionError: (error: unknown) => void}) {
  const open = (path: string) => {void api.request(path, 'empty-request', {method: 'POST', body: {}, requestContract: 'empty-request'}).catch(setActionError);};
  return <section className="diagnostics-surface" aria-labelledby="diagnostics-title"><header className="surface-header"><div><p className="eyebrow">System / Foundation</p><h1 id="diagnostics-title">Diagnostics</h1></div><button onClick={() => {setActionError(null); refresh();}}>Refresh</button></header>
    {error !== null && <ErrorState error={error}/>}
    {actionError !== null && <ErrorState error={actionError}/>}
    {!value ? <p role="status">Loading current run…</p> : <>

      <ConsolePanes panes={[
        {id: 'run', title: 'Current run', content: <><dl><dt>Application</dt><dd>{value.health.build.application_version}</dd><dt>Started</dt><dd>{displayTime(value.health.startup_utc_s)}</dd><dt>Uptime</dt><dd>{Math.floor(value.uptime_ms / 60000)} min {Math.floor(value.uptime_ms / 1000) % 60} sec</dd><dt>Run</dt><dd className="technical">{value.health.run_id}</dd><dt>Instance</dt><dd className="technical">{value.health.data_instance_id}</dd><dt>Readiness</dt><dd>{value.health.host_state}</dd><dt>Schema</dt><dd>Generation {value.health.migration_generation} / {value.health.last_migration_id}</dd><dt>Integrity</dt><dd>{value.health.integrity_state}</dd><dt>Source</dt><dd className="technical">{value.health.build.source_commit ?? 'Unavailable'}{value.health.build.dirty ? ' · modified' : ''}</dd></dl><details><summary>Canonical time evidence</summary><code>{new Date(value.health.startup_utc_s * 1000).toISOString()}</code></details></>},
        {id: 'activity', title: 'Runtime activity', content: <><dl><dt>Request tasks</dt><dd>{value.request_tasks} / 4 workers</dd><dt>Background tasks</dt><dd>{value.background_tasks} / 2 workers</dd><dt>Open connections</dt><dd>{value.open_connections ?? 'Measurement unavailable'}</dd><dt>Active transactions</dt><dd>{value.active_transactions ?? 'Measurement unavailable'}</dd></dl><h3>Durable jobs</h3>{value.job_counts ? <div className="metric-grid">{Object.entries(value.job_counts).map(([state, count]) => <span key={state}>{state.replaceAll('_', ' ')} <b>{count}</b></span>)}</div> : <p>Job counts unavailable</p>}</>},
        {id: 'capabilities', title: 'Capabilities', content: <><ul className="capability-list">{value.capabilities.map(item => <li key={item.id}><span>{item.id}</span><span>{item.state}</span></li>)}</ul></>},
        {id: 'logs', title: 'Operator logs', content: <><p>{value.logging_available ? 'Sanitized logging active' : 'Logging unavailable — console fallback'}</p><code>{value.current_log}</code><div className="button-row"><button onClick={() => open('/api/v1/diagnostics/open-log')}>Open current log</button><button onClick={() => open('/api/v1/diagnostics/open-folder')}>Open logs folder</button></div><h3>Runtime chronology</h3><ol className="runtime-events" aria-label="Runtime chronology">{value.runtime_events.map((event, i) => <li key={i}><time dateTime={new Date(event.recorded_at_utc_s * 1000).toISOString()}>{displayTime(event.recorded_at_utc_s)}</time><span>{event.code}</span></li>)}</ol><h3>Warnings / errors</h3>{value.recent_codes.length ? <ul className="warning-codes" aria-label="Warnings and errors">{value.recent_codes.map((code, i) => <li key={i}>{code}</li>)}</ul> : <p className="empty-warning">No warnings or errors.</p>}</>},
      ]}/>{value.partial.length > 0 && <p role="status">Partial diagnostics: {value.partial.join(', ')}</p>}
    </>}
  </section>;
}
