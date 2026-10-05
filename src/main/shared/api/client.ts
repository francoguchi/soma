import type {BootstrapV1, ErrorEnvelopeV1} from './generated/contracts';
import {assertContract} from './validate';
export class ApiError extends Error {
  constructor(readonly detail: ErrorEnvelopeV1) {super(detail.summary);}
}
export class ApiInputError extends Error {}
export class ApiClient {
  runId: string | null = null;
  csrf: string | null = null;
  async request<T>(path: string, contract: string, options: {method?: 'GET' | 'POST' | 'PUT' | 'PATCH'; body?: unknown; requestContract?: string; signal?: AbortSignal} = {}): Promise<T> {
    if (!path.startsWith('/api/v1/') || /[#\\]/u.test(path)) throw new ApiInputError('Unregistered API destination.');
    const method = options.method ?? 'GET';
    const headers: Record<string, string> = {'X-Correlation-ID': crypto.randomUUID()};
    if (this.runId) headers['X-SOMA-Run'] = this.runId;
    if (method !== 'GET') {
      if (!this.runId) throw new ApiInputError('Reload SOMA before continuing.');
      headers['Content-Type'] = 'application/json';
      if (this.csrf) headers['X-SOMA-CSRF'] = this.csrf;
      if (!options.requestContract) throw new ApiInputError('Missing command contract.');
      try {assertContract(options.requestContract, options.body);}
      catch {throw new ApiInputError('Request fields violate their accepted contract. Correct the input.');}
    }
    const init: RequestInit = {method, headers, credentials: 'same-origin', cache: 'no-store', redirect: 'error'};
    if (options.signal) init.signal = options.signal;
    if (method !== 'GET') init.body = JSON.stringify(options.body);
    const response = await fetch(path, init);
    const value: unknown = await response.json();
    if (!response.ok) throw new ApiError(assertContract<ErrorEnvelopeV1>('error-envelope', value));
    return assertContract<T>(contract, value);
  }
  acceptBootstrap(value: BootstrapV1) {
    if (this.runId && this.runId !== value.run_id) throw new Error('SOMA restarted. Reload this page.');
    this.runId = value.run_id; this.csrf = value.csrf_token;
  }
}
export const api = new ApiClient();
export class QueryController<T> {
  private sequence = 0;
  private abort: AbortController | null = null;
  async query(load: (signal: AbortSignal) => Promise<T>, publish: (value: T) => void, fail: (error: unknown) => void) {
    this.abort?.abort(); this.abort = new AbortController();
    const sequence = ++this.sequence;
    try {const value = await load(this.abort.signal); if (sequence === this.sequence) publish(value);}
    catch (error) {if (sequence === this.sequence && !this.abort.signal.aborted) fail(error);}
  }
  cancel() {++this.sequence; this.abort?.abort();}
}
