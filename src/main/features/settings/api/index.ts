import {api} from '../../../shared/api/client';
import type * as Contracts from '../../../shared/api/generated/contracts';
export const settingsApi = {
  getSetting(params: { setting_key: string; }, query: Contracts.ReferenceGetSettingRequestV1 = {}) { const search = new URLSearchParams(Object.entries(query).map(([key,value]) => [key,String(value)])); return api.request<Contracts.ReferenceSettingValueV1>(`/api/v1/settings/${encodeURIComponent(params.setting_key)}${search.size ? '?' + search.toString() : ''}`, 'urn:soma:01:setting-value:v1'); },
  writeSetting(params: { setting_key: string; }, body: Contracts.ReferenceWriteSettingRequestV1) { return api.request<Contracts.ReferenceSettingValueV1>(`/api/v1/settings/${encodeURIComponent(params.setting_key)}`, 'urn:soma:01:setting-value:v1', {method: 'PUT', body, requestContract: 'urn:soma:01:write-setting-request:v1'}); },
};
