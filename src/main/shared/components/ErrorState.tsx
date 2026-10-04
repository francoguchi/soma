import {ApiError} from '../api/client';
export function ErrorState({error, retry}: {error: unknown; retry?: () => void}) {
  const message = error instanceof Error ? error.message : 'This operation could not be completed.';
  return <div role="alert" className="error-state"><strong>Unable to continue</strong><p>{message}</p>{error instanceof ApiError && <small>{error.detail.code} · Request {error.detail.correlation_id}</small>}{retry && <button onClick={retry}>Try again</button>}</div>;
}
