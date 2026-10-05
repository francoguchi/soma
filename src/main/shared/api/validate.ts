import {schemas} from './generated/schemas';
type Schema = Record<string, unknown>;
const catalog = schemas as unknown as Record<string, Schema>;
function equal(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) && Array.isArray(right)) return left.length === right.length && left.every((item, index) => equal(item, right[index]));
  if (left && right && typeof left === 'object' && typeof right === 'object') {
    const a = left as Record<string, unknown>, b = right as Record<string, unknown>;
    return Object.keys(a).length === Object.keys(b).length && Object.keys(a).every(key => Object.hasOwn(b, key) && equal(a[key], b[key]));
  }
  return false;
}
function valid(schema: Schema, value: unknown): boolean {
  if (Array.isArray(schema['anyOf'])) return schema['anyOf'].some(choice => valid(choice as Schema, value));
  if (Array.isArray(schema['oneOf'])) return schema['oneOf'].filter(choice => valid(choice as Schema, value)).length === 1;
  if (typeof schema['$ref'] === 'string') {
    const [id, fragment] = schema['$ref'].split('#');
    let target: unknown = id ? catalog[id] : undefined;
    if (fragment) for (const part of fragment.split('/').slice(1)) target = (target as Schema)?.[part.replace(/~1/g, '/').replace(/~0/g, '~')];
    return !!target && valid(target as Schema, value);
  }
  if ('const' in schema && !equal(value, schema['const'])) return false;
  if (Array.isArray(schema['enum']) && !schema['enum'].some(option => equal(option, value))) return false;
  const types = Array.isArray(schema['type']) ? schema['type'] : [schema['type']];
  const kind = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
  if (!types.includes(kind) && !(kind === 'number' && types.includes('integer') && Number.isSafeInteger(value))) return false;
  if (value === null) return true;
  if (typeof value === 'string') {
    if (Array.from(value).some(character => {const code = character.codePointAt(0)!; return code >= 0xd800 && code <= 0xdfff;})) return false;
    const length = Array.from(value).length;
    if (typeof schema['minLength'] === 'number' && length < schema['minLength'] || typeof schema['maxLength'] === 'number' && length > schema['maxLength']) return false;
    if (typeof schema['pattern'] === 'string' && !new RegExp(schema['pattern'], 'u').test(value)) return false;
    return true;
  }
  if (typeof value === 'number') return Number.isFinite(value) && (typeof schema['minimum'] !== 'number' || value >= schema['minimum']) && (typeof schema['maximum'] !== 'number' || value <= schema['maximum']) && (typeof schema['exclusiveMinimum'] !== 'number' || value > schema['exclusiveMinimum']) && (typeof schema['exclusiveMaximum'] !== 'number' || value < schema['exclusiveMaximum']) && (typeof schema['multipleOf'] !== 'number' || Number.isInteger(value / schema['multipleOf']));
  if (Array.isArray(value)) return (typeof schema['minItems'] !== 'number' || value.length >= schema['minItems']) && (typeof schema['maxItems'] !== 'number' || value.length <= schema['maxItems']) && (schema['uniqueItems'] !== true || value.every((item, index) => !value.slice(0, index).some(prior => equal(prior, item)))) && value.every(item => valid(schema['items'] as Schema, item));
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const properties = schema['properties'] as Record<string, Schema>;
    return (schema['required'] as string[]).every(name => Object.hasOwn(record, name)) && Object.entries(record).every(([key, item]) => Object.hasOwn(properties, key) && valid(properties[key]!, item));
  }
  return true;
}
export function assertContract<T>(name: string, value: unknown): T {
  const schema = catalog[name.startsWith('urn:soma:') ? name : `urn:soma:00:${name}:v1`];
  if (!schema || !valid(schema, value)) throw new Error('Local API contract mismatch. Reload or rebuild SOMA.');
  return value as T;
}
