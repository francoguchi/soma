import {useEffect, useId, useRef, useState} from 'react';
export type Option = Readonly<{id: string; label: string; eligible: boolean}>;
export type OptionsPage = Readonly<{items: readonly Option[]; continuation: string | null; partial: boolean; warnings: readonly string[]}>;
export function Autocomplete({label, search, choose, minimum = 2}: {label: string; search: (query: string, cursor: string | null, limit: number, signal: AbortSignal) => Promise<OptionsPage>; choose: (value: Option) => void; minimum?: number}) {
  if (!Number.isInteger(minimum) || minimum < 1 || minimum > 4) throw new Error('Autocomplete minimum must be 1–4.');
  const id = useId(), input = useRef<HTMLInputElement>(null), sequence = useRef(0), abort = useRef<AbortController | null>(null), acceptedText = useRef<string | null>(null);
  const [query, setQuery] = useState(''), [items, setItems] = useState<readonly Option[]>([]), [active, setActive] = useState(-1), [open, setOpen] = useState(false), [status, setStatus] = useState(`Enter at least ${minimum} characters.`), [page, setPage] = useState<OptionsPage | null>(null), [height, setHeight] = useState(240), [above, setAbove] = useState(false);
  const load = async (text: string, cursor: string | null, current: readonly Option[], identity: number) => {
    const controller = new AbortController(); abort.current?.abort(); abort.current = controller; setStatus('Loading suggestions…');
    try {
      const result = await search(text, cursor, Math.min(25, 50 - current.length), controller.signal);
      if (identity !== sequence.current || controller.signal.aborted) return;
      if (result.items.length > Math.min(25, 50 - current.length) || new Set([...current, ...result.items].map(item => item.id)).size !== current.length + result.items.length) throw new Error('Suggestion page exceeds its bound or repeats identity.');
      setItems([...current, ...result.items]); setPage(previous => current.length && previous ? {...result, warnings: [...new Set([...previous.warnings, ...result.warnings])]} : result); setActive(-1); setOpen(true);
      setStatus(result.items.length || current.length ? result.partial || result.continuation ? 'Partial results — more matches are available.' : 'Suggestions available.' : 'No matches.');
    } catch {if (identity === sequence.current && !controller.signal.aborted) setStatus('Suggestions unavailable. Change the query or retry.');}
  };
  useEffect(() => {
    const identity = ++sequence.current; abort.current?.abort(); setItems([]); setPage(null); setActive(-1); setOpen(false);
    if (acceptedText.current === query) {setStatus('Selected existing record.'); return;}
    if (Array.from(query).length < minimum) {setStatus(`Enter at least ${minimum} characters.`); return;}
    const timer = setTimeout(() => {void load(query, null, [], identity);}, 150);
    return () => {clearTimeout(timer); ++sequence.current; abort.current?.abort();};
  }, [query, minimum, search]);
  useEffect(() => {const update = () => {const rect = input.current?.getBoundingClientRect(); if (!rect) return; const bottom = innerHeight - rect.bottom - 16, top = rect.top - 16; setAbove(bottom < 120 && top > bottom); setHeight(Math.max(40, Math.min(320, bottom < 120 && top > bottom ? top : bottom)));}; update(); addEventListener('resize', update); addEventListener('scroll', update, true); return () => {removeEventListener('resize', update); removeEventListener('scroll', update, true);};}, [open]);
  const accept = (option: Option) => {if (option.eligible) {acceptedText.current = option.label; choose(option); setQuery(option.label); setOpen(false); setActive(-1);}};
  useEffect(() => {if (active >= 0 && open) document.getElementById(id + '-option-' + active)?.scrollIntoView({block: 'nearest'});}, [active, open, id]);
  return <div className="autocomplete"><label htmlFor={id}>{label}</label><input id={id} ref={input} role="combobox" aria-expanded={open} aria-autocomplete="list" aria-controls={id + '-list'} aria-activedescendant={active >= 0 && open ? id + '-option-' + active : undefined} value={query} onChange={event => {acceptedText.current = null; setQuery(event.target.value);}} onBlur={() => setOpen(false)} onKeyDown={event => {
    if (event.key === 'Escape' || event.key === 'Tab') {setOpen(false); setActive(-1); return;}
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {event.preventDefault(); setOpen(true); const eligible = items.map((option, i) => option.eligible ? i : -1).filter(i => i >= 0); const index = eligible.indexOf(active); setActive(eligible[Math.max(0, Math.min(eligible.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))] ?? -1);}
    if (event.key === 'Enter' && open) {event.preventDefault(); const option = items[active]; if (option) accept(option);}
  }}/>{open && <div className="autocomplete-popup" data-scroll-owner="y" style={{maxHeight: height, ...(above ? {bottom: '100%'} : {})}}><ul role="listbox" id={id + '-list'}>{items.map((option, index) => <li key={option.id} id={id + '-option-' + index} role="option" aria-selected={index === active} aria-disabled={!option.eligible} onPointerDown={event => event.preventDefault()} onClick={() => accept(option)}>{option.label}{!option.eligible && ' · Unavailable'}</li>)}</ul>{page?.continuation && items.length < 50 && <button type="button" onPointerDown={event => event.preventDefault()} onClick={() => {void load(query, page.continuation, items, sequence.current);}}>More suggestions</button>}{items.length >= 50 && <p>50 options loaded. Refine the query for other matches.</p>}</div>}<p role="status">{status}</p>{page?.warnings.map(warning => <p role="status" key={warning}>Warning: {warning}</p>)}</div>;
}
