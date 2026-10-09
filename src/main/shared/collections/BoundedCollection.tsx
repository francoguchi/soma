import {useEffect, useLayoutEffect, useRef, useState, type ReactNode} from 'react';
import {QueryController} from '../api/client';
import {ErrorState} from '../components/ErrorState';
export type Page<T> = Readonly<{items: readonly T[]; continuation: string | null; as_of_utc_s: number; partial: boolean; warnings: readonly string[]; total: number | null}>;
export function BoundedCollection<T>({queryKey, load, render, emptyMessage = 'No records in this page.', pageSize = 100, showEmptyCount = false, showCount = true, summary, retainQueries = false}: {queryKey: string; load: (cursor: string | null, limit: number, signal: AbortSignal) => Promise<Page<T>>; render: (page: Page<T>, stale: boolean) => ReactNode; emptyMessage?: string; pageSize?: number; showEmptyCount?: boolean; showCount?: boolean; summary?: (page: Page<T>, stale: boolean) => ReactNode; retainQueries?: boolean}) {
  const root = useRef<HTMLElement>(null);
  const memory = useRef(new Map<string, {cursor: string | null; page: Page<T>; scroll?: {top: number; left: number}}>());
  const [intent, setIntent] = useState<{key: string; cursor: string | null}>({key: queryKey, cursor: null});
  const [result, setResult] = useState<{key: string; page: Page<T>} | null>(null), [loading, setLoading] = useState(true), [error, setError] = useState<unknown>(null), [retry, setRetry] = useState(0);
  const page = result?.key === queryKey ? result.page : (retainQueries ? memory.current.get(queryKey)?.page : null) ?? result?.page ?? null;
  const cursor = intent.key === queryKey ? intent.cursor : retainQueries ? memory.current.get(queryKey)?.cursor ?? null : null;
  useLayoutEffect(() => {
    if (!retainQueries) return;
    const node = root.current?.querySelector<HTMLElement>('[data-scroll-owner]');
    const saved = memory.current.get(queryKey)?.scroll;
    if (node && saved) {node.scrollTop = saved.top; node.scrollLeft = saved.left;}
    return () => {
      const saved = memory.current.get(queryKey);
      if (node && saved) saved.scroll = {top: node.scrollTop, left: node.scrollLeft};
    };
  }, [queryKey, page, retainQueries]);
  useEffect(() => {
    const controller = new QueryController<Page<T>>(); setLoading(true); setError(null);
    void controller.query(signal => load(cursor, pageSize, signal), value => {
      if (value.items.length > 200) {setError(new Error('Collection exceeds the page bound. Refresh with a smaller owner query.')); setLoading(false); return;}
      if (retainQueries) {
        const scroll = memory.current.get(queryKey)?.scroll;
        memory.current.set(queryKey, {cursor, page: value, ...(scroll ? {scroll} : {})});
        // Retain a bounded number of query contexts; only one page is rendered.
        if (memory.current.size > 8) memory.current.delete(memory.current.keys().next().value!);
      }
      setResult({key: queryKey, page: value}); setLoading(false);
    }, caught => {setError(caught); setLoading(false);});
    return () => controller.cancel();
  }, [queryKey, cursor, retry, load, pageSize, retainQueries]);
  const stale = loading || error !== null || result?.key !== queryKey;
  return <section ref={root} aria-busy={loading}>{loading && <p role="status">{page ? 'Refreshing — the previous page is stale.' : 'Loading records…'}</p>}{error !== null && <ErrorState error={error} retry={() => setRetry(value => value + 1)}/>}{page && <div data-stale={stale}>{summary?.(page, stale)}{page.items.length ? render(page, stale) : emptyMessage && <p>{emptyMessage}</p>}{page.warnings.map(warning => <p role="status" key={warning}>Warning: {warning}</p>)}{showCount && (showEmptyCount || page.items.length > 0 || page.continuation) && <p>{page.total === null ? `${page.items.length} ${page.items.length === 1 ? 'record' : 'records'} in this page` : page.total === page.items.length && !cursor && !page.continuation ? `${page.total} ${page.total === 1 ? 'record' : 'records'}` : `${page.items.length} ${page.items.length === 1 ? 'record' : 'records'} in this page · ${page.total} matching ${page.total === 1 ? 'record' : 'records'}`}</p>}{(page.partial || page.continuation) && <p role="status">Additional results are available.</p>}{page.continuation && <button disabled={stale} onClick={() => setIntent({key: queryKey, cursor: page.continuation})}>Next page</button>}</div>}</section>;
}
