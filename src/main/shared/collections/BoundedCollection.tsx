import {useEffect, useState, type ReactNode} from 'react';
import {QueryController} from '../api/client';
import {ErrorState} from '../components/ErrorState';
export type Page<T> = Readonly<{items: readonly T[]; continuation: string | null; as_of_utc_s: number; partial: boolean; warnings: readonly string[]; total: number | null}>;
export function BoundedCollection<T>({queryKey, load, render, emptyMessage = 'No records in this page.'}: {queryKey: string; load: (cursor: string | null, limit: number, signal: AbortSignal) => Promise<Page<T>>; render: (page: Page<T>, stale: boolean) => ReactNode; emptyMessage?: string}) {
  const [intent, setIntent] = useState<{key: string; cursor: string | null}>({key: queryKey, cursor: null});
  const [page, setPage] = useState<Page<T> | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState<unknown>(null), [retry, setRetry] = useState(0);
  const cursor = intent.key === queryKey ? intent.cursor : null;
  useEffect(() => {
    const controller = new QueryController<Page<T>>(); setLoading(true); setError(null);
    void controller.query(signal => load(cursor, 100, signal), value => {
      if (value.items.length > 200) {setError(new Error('Collection exceeds the page bound. Refresh with a smaller owner query.')); setLoading(false); return;}
      setPage(value); setLoading(false);
    }, caught => {setError(caught); setLoading(false);});
    return () => controller.cancel();
  }, [queryKey, cursor, retry, load]);
  return <section aria-busy={loading}>{loading && <p role="status">{page ? 'Refreshing — the previous page is stale.' : 'Loading records…'}</p>}{error !== null && <ErrorState error={error} retry={() => setRetry(value => value + 1)}/>}{page && <div data-stale={loading || error !== null}>{page.items.length ? render(page, loading || error !== null) : <p>{emptyMessage}</p>}{page.warnings.map(warning => <p role="status" key={warning}>Warning: {warning}</p>)}<p>{page.total === null ? `${page.items.length} records in this page` : `${page.items.length} records in this page · ${page.total} matching records`}</p>{(page.partial || page.continuation) && <p role="status">Additional results are available. Selection and draft context are retained.</p>}{page.continuation && <button disabled={loading || error !== null} onClick={() => setIntent({key: queryKey, cursor: page.continuation})}>Next page</button>}</div>}</section>;
}
