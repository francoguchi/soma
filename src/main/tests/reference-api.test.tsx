import {afterEach, expect, test, vi} from 'vitest';
import {ApiClient} from '../shared/api/client';
import {assertContract} from '../shared/api/validate';

afterEach(() => vi.unstubAllGlobals());

test('Scope-01 bindings validate closed bounded inputs using their full contract IDs', () => {
  const contract = 'urn:soma:01:match-customer-request:v1';
  expect(assertContract(contract, {raw_name: 'Customer', limit: 200})).toEqual({raw_name: 'Customer', limit: 200});
  expect(() => assertContract(contract, {raw_name: 'Customer', limit: 201})).toThrow();
  expect(() => assertContract(contract, {raw_name: 'Customer', actor_id: 'caller'})).toThrow();
});

test.each(['PUT', 'PATCH'] as const)('shared client carries authenticated %s commands and validates their result', async method => {
  const client = new ApiClient();
  client.runId = 'run'; client.csrf = 'csrf';
  const id = '4d204e28-3a66-43cb-81ca-a31cc94c9b11';
  const result = {outcome: 'APPLIED', target_id: id, revision: 2, result_refs: [{type: 'customer_organization', id}]};
  const fetch = vi.fn(async (_path: string, _init: RequestInit) => ({ok: true, json: async () => result}));
  vi.stubGlobal('fetch', fetch);
  const requestContract = method === 'PUT' ? 'set-account-code-request' : 'update-customer-request';
  const body = {command_id: id, base_revision: 1, ...(method === 'PUT' ? {account_code: 'CODE'} : {name: 'Customer'})};
  expect(await client.request('/api/v1/reference/customer-organizations/' + id, 'urn:soma:01:mutation-result:v1', {
    method, body, requestContract: `urn:soma:01:${requestContract}:v1`,
  })).toEqual(result);
  expect(fetch.mock.calls[0]?.[1]).toMatchObject({method, headers: {'X-SOMA-Run': 'run', 'X-SOMA-CSRF': 'csrf'}, body: JSON.stringify(body)});
});
