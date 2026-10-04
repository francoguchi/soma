import {useId, useRef} from 'react';
import {isNestedControl, selectionOpen, type Row, type Selection} from '../interactions/selection';
export function SelectableCollection({rows, selection, change, open, multi = false}: {rows: readonly (Row & {label: string})[]; selection: Selection; change: (value: Selection) => void; open: (row: Row) => void; multi?: boolean}) {
  const id = useId(), elements = useRef(new Map<string, HTMLDivElement>());
  const eligible = rows.filter(row => row.eligible);
  const dispatchOpen = (row: Row, nestedControl: boolean) => {if (row.eligible && row.route && !nestedControl) {change(selectionOpen(selection, {kind: 'open', row, nestedControl})); open(row);}};
  return <div><div role="grid" aria-label="Records" aria-multiselectable={multi} data-scroll-owner="y" className="selectable-collection">{rows.map(row => <div key={row.id} ref={node => {if (node) elements.current.set(row.id, node); else elements.current.delete(row.id);}} role="row" aria-selected={multi ? selection.member_ids.includes(row.id) : selection.selected_id === row.id} aria-disabled={!row.eligible} tabIndex={row.eligible && (selection.active_id === row.id || !eligible.some(item => item.id === selection.active_id) && eligible[0]?.id === row.id) ? 0 : -1} data-focus-token={'record:' + row.id} className={selection.active_id === row.id ? 'active-row' : ''}
    onClick={event => {const nested = isNestedControl(event.target, event.currentTarget); if (!nested) {change(selectionOpen(selection, {kind: 'click', row, nestedControl: false})); event.currentTarget.focus();}}}
    onDoubleClick={event => dispatchOpen(row, isNestedControl(event.target, event.currentTarget))}
    onKeyDown={event => {
      if (isNestedControl(event.target, event.currentTarget)) return;
      if (event.key === 'Enter') {event.preventDefault(); dispatchOpen(row, false);}
      else if (event.key === ' ') {event.preventDefault(); change(selectionOpen(selection, {kind: 'space', row, multi}));}
      else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault(); const index = eligible.findIndex(item => item.id === row.id);
        const next = eligible[event.key === 'Home' ? 0 : event.key === 'End' ? eligible.length - 1 : Math.max(0, Math.min(eligible.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))];
        if (next) {change(selectionOpen(selection, {kind: 'arrow', row: next, selectionFollowsFocus: false})); elements.current.get(next.id)?.focus();}
      }
    }}><span role="gridcell">{multi && <input aria-label={'Select ' + row.label} type="checkbox" disabled={!row.eligible} checked={selection.member_ids.includes(row.id)} onChange={() => change(selectionOpen(selection, {kind: 'space', row, multi: true}))}/>}<span id={id + row.id}>{row.label}</span></span><span role="gridcell"><button aria-label={'Open ' + row.label} disabled={!row.eligible || !row.route} onClick={() => dispatchOpen(row, false)}>Open</button></span></div>)}</div>{selection.member_ids.some(identity => !rows.some(row => row.id === identity)) && <p role="status">Selections outside this page are retained.</p>}</div>;
}
