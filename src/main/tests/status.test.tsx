import {afterEach, expect, test} from 'vitest';
import {cleanup, render, screen} from '@testing-library/react';
import {OperatorStatus} from '../app/status/OperatorStatus';
import type {BootstrapV1, DiagnosticsV1} from '../shared/api/generated/contracts';
import {buildIdentity} from '../shared/build/identity';

afterEach(cleanup);
const run = '00000000-0000-4000-8000-000000000001';
const bootstrap: BootstrapV1 = {run_id: run, build: buildIdentity, auth_state: 'authenticated', csrf_token: null, capabilities: []};
const value: DiagnosticsV1 = {
  health: {protocol_version: 1, run_id: run, data_instance_id: '00000000-0000-4000-8000-000000000002', host_state: 'READY', build: buildIdentity, pid: 1, process_birth_id: '1', migration_generation: 6, last_migration_id: 'M00.005', schema_state: 'current', integrity_state: 'verified', startup_utc_s: 1000},
  uptime_ms: 0, capabilities: [], job_counts: null, request_tasks: 0, background_tasks: 0, open_connections: null, active_transactions: null, current_log: 'diagnostics/run.jsonl', logging_available: true, recent_codes: [], runtime_events: [], partial: [],
};
test('status preserves bounded provider facts and never guesses readiness or schema', () => {
  const {rerender} = render(<OperatorStatus bootstrap={bootstrap} diagnostics={null}/>);
  expect(screen.getByText('Checking')).toBeTruthy();
  expect(screen.getAllByText('schema unavailable')).toHaveLength(2);
  rerender(<OperatorStatus bootstrap={bootstrap} diagnostics={value}/>);
  expect(screen.getByText('READY')).toBeTruthy();
  expect(screen.getByLabelText('Operator status').dataset['condition']).toBe('ready');
  expect(screen.getByLabelText('Operator status').textContent).toContain('run 00000000');
  expect(screen.getByLabelText('Operator status').textContent).not.toContain(run);
  expect(screen.getByLabelText('Operator status').textContent).not.toContain('diagnostics/run.jsonl');
  rerender(<OperatorStatus bootstrap={bootstrap} diagnostics={{...value, health: {...value.health, run_id: 'other'}}}/>);
  expect(screen.getByText('Checking')).toBeTruthy();
});
test('pre-ready, failed, partial and unreachable states stay factual and distinct', () => {
  const {rerender} = render(<OperatorStatus bootstrap={bootstrap} diagnostics={{...value, health: {...value.health, host_state: 'SERVING_NOT_READY'}}}/>);
  expect(screen.getByText('SERVING_NOT_READY')).toBeTruthy();
  rerender(<OperatorStatus bootstrap={bootstrap} diagnostics={{...value, partial: ['jobs']}}/>);
  expect(screen.getByText('READY / DEGRADED')).toBeTruthy();
  expect(screen.getByLabelText('Operator status').dataset['condition']).toBe('degraded');
  rerender(<OperatorStatus bootstrap={bootstrap} diagnostics={{...value, health: {...value.health, host_state: 'FAILED'}}}/>);
  expect(screen.getByText('FAILED')).toBeTruthy();
  expect(screen.getByLabelText('Operator status').dataset['condition']).toBe('degraded');
  rerender(<OperatorStatus bootstrap={bootstrap} diagnostics={value} unavailable/>);
  expect(screen.getByText('Unavailable')).toBeTruthy();
  expect(screen.getByLabelText('Operator status details')).toBeTruthy();
});
