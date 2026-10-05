import {useState, type RefObject} from 'react';
import {api} from '../../shared/api/client';
import type * as C from '../../shared/api/generated/contracts';
import {settingsApi} from './api';
import {useWorkingIntent} from '../../shared/interactions/use-working-intent';
import {applyAppearance} from '../../shared/appearance';
import {AppearancePreference, appearanceRegistration} from '../../shared/appearance-preference';
import {QueryState, useOwnerAction, useOwnerQuery} from '../reference/model';

function Preference({definition, application}: {definition: C.ReferenceSettingsDefinitionsV1['items'][number]; application: RefObject<HTMLElement | null>}) {
  const query = useOwnerQuery<C.ReferenceSettingValueV1>(definition.setting_key, signal => api.request('/api/v1/settings/' + encodeURIComponent(definition.setting_key), 'urn:soma:01:setting-value:v1', {signal}));
  return <><QueryState query={query}/>{query.value && <PreferenceEditor key={definition.setting_key} value={query.value} application={application} refresh={query.reload}/>}</>;
}
function PreferenceEditor({value, application, refresh}: {value: C.ReferenceSettingValueV1; application: RefObject<HTMLElement | null>; refresh: () => void}) {
  const working = useWorkingIntent({value_json: value.value_json}, {contract_id: 'reference.edit.setting', contract_version: 1, target_type: 'setting', target_id: value.setting_key, scope_key: 'metadata', base_revision: value.revision === null ? 'ABSENT' : String(value.revision)}, application);
  const action = useOwnerAction();
  const appearance = Object.entries(appearanceRegistration).every(([key, expected]) => value[key as keyof typeof appearanceRegistration] === expected);
  if (!appearance) return <><h3>{value.contract_name}</h3><p>{value.source} · owner {value.semantic_owner}</p><p>This registered setting requires its owner's presentation panel. Arbitrary key/value editing is unavailable.</p></>;
  return <><h3>Appearance</h3><p>{value.source} · {value.revision === null ? 'No persisted override' : 'revision ' + value.revision}</p><form className="operational-form" onSubmit={e => {e.preventDefault(); void action.run(JSON.stringify({key: value.setting_key, revision: value.revision, draft: working.draft}), command => settingsApi.writeSetting({setting_key: value.setting_key}, {command_id: command, base_revision: value.revision, semantic_owner: value.semantic_owner, contract_name: value.contract_name, contract_version: value.contract_version, value_json: working.draft.value_json}), async () => {await working.accepted(); applyAppearance(JSON.parse(working.draft.value_json)); refresh();});}}><AppearancePreference valueJson={working.draft.value_json} change={json => working.edit('value_json', json)} disabled={action.busy || action.pending}/><button disabled={action.busy || working.conflict}>Save appearance preference explicitly</button></form>{working.recovery}{action.feedback}</>;
}
export function Preferences({application}: {application: RefObject<HTMLElement | null>}) {
  const query = useOwnerQuery<C.ReferenceSettingsDefinitionsV1>('settings-definitions', signal => api.request('/api/v1/settings/registry/definitions', 'urn:soma:01:settings-definitions:v1', {signal}));
  const [key, setKey] = useState('foundation.appearance');
  return <><QueryState query={query}/>{query.value && <><label>Registered preference<select value={key} onChange={e => setKey(e.target.value)}>{query.value.items.map(row => <option key={row.setting_key} value={row.setting_key}>{row.contract_name === 'AppearancePreferenceV1' ? 'Appearance' : row.contract_name} · {row.semantic_owner}</option>)}</select></label>{query.value.items.find(row => row.setting_key === key) && <Preference definition={query.value.items.find(row => row.setting_key === key)!} application={application}/>}</>}</>;
}
