import {useId, type ReactNode} from 'react';
import {SomaIcon} from './SomaIcon';
import {Action} from './Section';

export type SearchSource = 'available' | 'empty' | 'loading' | 'unavailable';
export function CollectionSearch({label, source, reason, children, compact = false}: {label: string; source: SearchSource; reason?: string; children?: ReactNode; compact?: boolean}) {
  const id = useId();
  const explanation = reason ?? (source === 'empty' ? 'No active records to search yet.' : source === 'loading' ? 'Loading search availability…' : 'Search is unavailable.');
  return <section className="collection-search" role="search" aria-label={label} data-search-source={source}>
    {!compact && <h3><SomaIcon name="search"/>{label}</h3>}
    {source !== 'available' && <p id={id} role="status">{explanation}</p>}
    <fieldset disabled={source !== 'available'} aria-describedby={source !== 'available' ? id : undefined}>{children}</fieldset>
  </section>;
}

export function SearchToolbar({label, source, reason, value, change, search, clear, canClear, advanced, toggleAdvanced, advancedId}: {
  label: string; source: SearchSource; reason?: string; value: string; change: (value: string) => void;
  search: () => void; clear: () => void; canClear: boolean; advanced: boolean; toggleAdvanced: () => void; advancedId: string;
}) {
  return <div className="search-controls"><CollectionSearch label={label} source={source} {...(reason ? {reason} : {})} compact>
    <form className="search-toolbar" onSubmit={event => {event.preventDefault(); if (source === 'available') search();}}>
      <label className="search-input"><SomaIcon name="search"/><span className="sr-only">{label}</span><input value={value} placeholder={label} onChange={event => change(event.target.value)} onKeyDown={event => {if (event.key === 'Escape') {event.preventDefault(); clear();}}}/></label>
      <Action type="submit" icon="search" disabled={!value.trim()}>Search</Action>
    </form>
  </CollectionSearch><div role="group" aria-label="Search actions" className="form-actions">
    <Action onClick={clear} disabled={!canClear}>Clear search</Action><Action aria-expanded={advanced} aria-controls={advancedId} onClick={toggleAdvanced}>Advanced search</Action>
  </div></div>;
}
