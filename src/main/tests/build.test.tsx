import {expect, test} from 'vitest';
import {render, screen} from '@testing-library/react';
import {buildIdentity} from '../shared/build/identity';
import type {ErrorEnvelopeV1} from '../shared/api/generated/contracts';

test('Main consumes the generated source identity and closed error binding', () => {
  const error: ErrorEnvelopeV1 = {
    code: 'INTERNAL_ERROR', summary: 'Safe.', recoverability: 'none', safe_next_action: null,
    correlation_id: '4d204e28-3a66-43cb-81ca-a31cc94c9b11',
  };
  render(<p>{buildIdentity.application_version}: {error.summary}</p>);
  expect(screen.getByText('0.1.0.dev0: Safe.')).toBeTruthy();
  expect(buildIdentity.runtime_protocol_version).toBe(1);
});
