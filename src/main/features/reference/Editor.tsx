import {SectionHeading, FormActions, Action} from '../../shared/components/Section';
import {type RefObject} from 'react';
import {DispatchAddress} from './dispatch/Address';
import {referenceApi as commands} from './api';
import type * as C from '../../shared/api/generated/contracts';
import {useWorkingIntent} from '../../shared/interactions/use-working-intent';
import {CustomerChooser, Field, useOwnerAction, type Detail, type Kind} from './model';

export function Editor({kind, id, detail, application, accepted, cancel}: {kind: Kind; id: string; detail: Detail | null; application: RefObject<HTMLElement | null>; accepted: (id: string) => void; cancel?: () => void}) {
  const creating = detail === null;
  const singular = kind === 'customer_organization' ? 'Customer' : kind === 'contact' ? 'Contact' : 'Dispatch Location';
  const dispatch = detail && 'address_mode' in detail ? detail as C.ReferenceDispatchDetailV1 : null;
  const initial = kind === 'customer_organization' ? {name: detail?.name ?? '', account_code: ''} : kind === 'contact' ? {name: detail?.name ?? '', email: '', customer_id: ''} : {name: detail?.name ?? '', address: dispatch?.standalone_address_text ?? ''};
  const working = useWorkingIntent(initial as Record<string, string>, {contract_id: 'reference.edit.' + kind, contract_version: 1, target_type: kind, target_id: id, scope_key: 'metadata', base_revision: detail ? String(detail.revision) : 'NEW'}, application);
  const {draft, edit} = working, action = useOwnerAction();
  const inactive = detail?.lifecycle_state === 'archived';
  const save = async (command: string) => {
    if (creating) {
      if (kind === 'customer_organization') return commands.createCustomer({command_id: command, name: draft['name']!, account_code: draft['account_code'] || null});
      if (kind === 'contact') return commands.createContact({command_id: command, name: draft['name']!, initial_email: draft['email'] || null, initial_customer_org_id: draft['customer_id'] || null});
      return commands.createDispatch({command_id: command, name: draft['name']!, address_text: draft['address']!});
    }
    const body = {command_id: command, base_revision: detail.revision, name: draft['name']!};
    if (kind === 'customer_organization') return commands.updateCustomer({id}, body);
    if (kind === 'contact') return commands.updateContact({id}, body);
    return commands.updateDispatch({id}, {...body, ...(dispatch?.address_mode === 'standalone' ? {address_text: draft['address']!} : {})});
  };
  return <>{!creating && <SectionHeading level={3} icon={kind === 'customer_organization' ? 'customer' : kind === 'contact' ? 'contact' : 'dispatch'}>{detail.name}</SectionHeading>}{detail && <p>Revision {detail.revision} · {detail.lifecycle_state}{inactive ? ' — history only until explicit reactivation' : ''}</p>}
    <form className="operational-form" onSubmit={e => {e.preventDefault(); void action.run(JSON.stringify({id, revision: detail?.revision, draft}), async command => {
      const result = await save(command); await working.accepted(); accepted(result.target_id); return result;
    }, () => {});}}><fieldset disabled={action.busy || action.pending || inactive}><div className="operational-form">
      <Field label="Name" value={draft['name']!} change={v => edit('name', v)} required/>
      {creating && kind === 'customer_organization' && <Field label="Initial Account Code (optional)" value={draft['account_code']!} change={v => edit('account_code', v)} maximum={512}/>}
      {creating && kind === 'contact' && <><Field label="Initial email (optional)" value={draft['email']!} change={v => edit('email', v)} maximum={2048}/><CustomerChooser value={draft['customer_id']!} change={v => edit('customer_id', v)}/><p>Email and Customer are optional.</p></>}
      {kind === 'dispatch_location' && <DispatchAddress detail={dispatch} value={draft['address']!} change={v => edit('address', v)}/>}
      <FormActions>{creating && <Action onClick={cancel}>Cancel</Action>}<Action type="submit" variant="command" disabled={working.conflict || (!creating && !working.dirty)}>{action.busy ? 'Saving…' : creating ? 'Create ' + singular : kind === 'dispatch_location' && dispatch?.address_mode === 'standalone' ? 'Save name and standalone address' : 'Save name'}</Action></FormActions>
    </div></fieldset></form>{working.recovery}{action.feedback}
  </>;
}
