import {useCallback, useEffect, useRef, useState} from 'react';
import {api, QueryController} from '../../shared/api/client';
import type {DiagnosticsV1} from '../../shared/api/generated/contracts';

export function useDiagnostics(runId: string | null) {
  const [value, setValue] = useState<DiagnosticsV1 | null>(null);
  const [error, setError] = useState<unknown>(null);
  const refreshRef = useRef<() => void>(() => {});
  const refresh = useCallback(() => refreshRef.current(), []);
  useEffect(() => {
    setValue(null); setError(null);
    if (!runId) {refreshRef.current = () => {}; return;}
    const query = new QueryController<DiagnosticsV1>();
    const load = () => {void query.query(signal => api.request('/api/v1/diagnostics', 'diagnostics', {signal}), next => {
      if (next.health.run_id !== runId) {setError(new Error('SOMA restarted. Reload to reconnect.')); return;}
      setValue(next); setError(null);
    }, setError);};
    refreshRef.current = load; load();
    const interval = setInterval(load, 10000);
    return () => {clearInterval(interval); query.cancel(); refreshRef.current = () => {};};
  }, [runId]);
  return {value, error, refresh};
}
