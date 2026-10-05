import type {ReferenceDispatchDetailV1} from '../../../shared/api/generated/contracts';
import {Field} from '../model';

export function DispatchAddress({detail, value, change}: {detail: ReferenceDispatchDetailV1 | null; value: string; change: (value: string) => void}) {
  return detail?.address_mode === 'site_derived' ? <><p>Site-derived address · {detail.current_address.state}. Address changes belong to Infrastructure.</p><p>{detail.current_address.address_text ?? 'Current Site address is unavailable.'}</p></> : <Field label="Standalone address" value={value} change={change} required multiline maximum={8192}/>;
}
