import {type RefObject} from 'react';
import {api} from '../../../shared/api/client';
import type * as C from '../../../shared/api/generated/contracts';
import {useWorkingIntent} from '../../../shared/interactions/use-working-intent';
import {referenceApi} from '../../reference/api';
import {Field, QueryState, useOwnerAction, useOwnerQuery} from '../../reference/model';

function ProfileEditor({value, application, refresh}: {value: C.ReferenceProfileDetailV1; application: RefObject<HTMLElement | null>; refresh: () => void}) {
  const working = useWorkingIntent({display_name: value.display_name}, {contract_id: 'reference.edit.local_user_profile', contract_version: 1, target_type: 'local_user_profile', target_id: value.local_user_profile_id, scope_key: 'metadata', base_revision: String(value.revision)}, application);
  const action = useOwnerAction();
  return <><p>Current display name: {value.display_name}.</p><p>Your display name appears in the application. The default is Local Administrator.</p><form className="operational-form" onSubmit={e => {e.preventDefault(); void action.run(JSON.stringify({revision: value.revision, draft: working.draft}), command => referenceApi.updateProfile({command_id: command, base_revision: value.revision, display_name: working.draft.display_name}), async () => {await working.accepted(); dispatchEvent(new Event('soma:profile-updated')); refresh();});}}>
    <Field label="Display name" value={working.draft.display_name} change={v => working.edit('display_name', v)} maximum={512} required disabled={action.busy || action.pending}/><button disabled={action.busy || !working.dirty || working.conflict}>Save display name</button>
  </form><p>Display name does not change sign-in or credentials.</p>{working.recovery}{action.feedback}{action.error !== null && <button onClick={refresh}>Reload display name and review changes</button>}</>;
}
export function Profile({application}: {application: RefObject<HTMLElement | null>}) {
  const query = useOwnerQuery<C.ReferenceProfileDetailV1>('profile', signal => api.request('/api/v1/local-user-profile', 'urn:soma:01:profile-detail:v1', {signal}));
  return <><QueryState query={query}/>{query.value && <ProfileEditor value={query.value} application={application} refresh={query.reload}/>}</>;
}
