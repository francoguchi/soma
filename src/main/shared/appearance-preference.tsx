import {ConsoleComment} from './components/Section';
/** Foundation owns appearance meaning; Settings supplies storage and presentation orchestration. */
export const appearanceRegistration = Object.freeze({setting_key: 'foundation.appearance', semantic_owner: 'foundation', contract_name: 'AppearancePreferenceV1', contract_version: 1});
export function AppearancePreference({valueJson, change, disabled, label = 'Appearance preference'}: {label?: string; valueJson: string; change: (json: string) => void; disabled: boolean}) {
  let value = '';
  try {const candidate: unknown = JSON.parse(valueJson); if (candidate === 'core_dark' || candidate === 'system' || candidate === 'light') value = candidate;} catch { /* Preserve invalid recovery intent until explicit correction. */ }
  return <><label>{label}<select value={value} onChange={event => change(JSON.stringify(event.target.value))} disabled={disabled} required>
    {!value && <option value="">Choose a supported preference explicitly</option>}<option value="core_dark">SOMA Core Dark</option><option value="system">System preference (future support)</option><option value="light">Light preference (future support)</option>
  </select></label>{!value && <p role="alert">Recovered appearance intent requires an explicit valid choice.</p>}<ConsoleComment>System and Light are retained for future support.</ConsoleComment></>;
}
