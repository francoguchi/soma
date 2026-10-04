export function applyAppearance(preference: unknown = null): 'core-dark' {
  void preference;
  document.documentElement.dataset['appearance'] = 'core-dark';
  return 'core-dark';
}
