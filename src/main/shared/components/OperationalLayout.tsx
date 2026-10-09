import {useId, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode} from 'react';
import {clampRatio, defaultRatios, readRatios, rememberRatios} from '../interactions/panel-ratios';
import {ConsoleCue} from './ConsoleCue';

type Pane = {title: string; content: ReactNode; actions?: ReactNode};
/** Owner-neutral collection anchor; owners supply accepted truth, forms and guards. */
export function OperationalLayout({sessionKey, collection, details, context, focusRequest}: {
  sessionKey: string; collection: Pane; details?: Pane; context?: Pane; focusRequest?: string;
}) {
  const root = useRef<HTMLDivElement>(null), lower = useRef<HTMLDivElement>(null), id = useId();
  const [ratios, setRatios] = useState(() => readRatios(sessionKey));
  const [size, setSize] = useState({width:1000, height:700});
  const [split, setSplit] = useState(false), [active, setActive] = useState('collection');
  const available = ['collection', ...(details ? ['details'] : []), ...(details && context ? ['context'] : [])];
  const current = available.includes(active) ? active : 'collection';
  useLayoutEffect(() => {setRatios(readRatios(sessionKey));}, [sessionKey]);
  useLayoutEffect(() => {
    const node = root.current!;
    const update = () => {
      const rect = node.getBoundingClientRect();
      const width = node.clientWidth || rect.width, height = node.clientHeight || rect.height;
      const wide = width >= 720 && height >= 450;
      setSize({width:width - 8,height:height - (node.querySelector('.operational-layout-controls')?.clientHeight ?? 0) - 8});
      const focused = document.activeElement?.closest<HTMLElement>('[data-operational-pane]');
      if (focused && node.contains(focused)) setActive(focused.dataset['operationalPane']!);
      setSplit(wide);
    };
    const observer = new ResizeObserver(update); observer.observe(node); update();
    return () => observer.disconnect();
  }, [!!details]);
  useLayoutEffect(() => {
    if (!split) return;
    setRatios(previous => ({upper:clampRatio(previous.upper,size.height,160),left:clampRatio(previous.left,size.width,260)}));
  }, [split,size.width,size.height]);
  useLayoutEffect(() => {
    if (focusRequest && details) {
      setActive('details'); root.current?.querySelector<HTMLElement>('[data-operational-pane=details]')?.focus({preventScroll: true});
    }
  }, [focusRequest]);
  useLayoutEffect(() => {
    const node = root.current!, focused = document.activeElement;
    if (focused instanceof HTMLElement && node.contains(focused) && focused.closest('[hidden]')) {
      node.querySelector<HTMLElement>(`[data-operational-pane="${current}"]`)?.focus({preventScroll: true});
    }
  }, [split, current, !!details, !!context]);
  const changeRatio = (axis: 'upper' | 'left', value: number) => {
    const extent = axis === 'upper' ? size.height : size.width;
    setRatios(previous => {const next = {...previous, [axis]: clampRatio(value, extent, axis === 'upper' ? 160 : 260)}; rememberRatios(sessionKey, next); return next;});
  };
  const separator = (axis: 'upper' | 'left') => <div className="panel-separator" role="separator" tabIndex={0}
    aria-label={axis === 'upper' ? 'Collection and inspector size' : 'Details and Context size'}
    aria-orientation={axis === 'upper' ? 'horizontal' : 'vertical'} aria-valuemin={Math.ceil(clampRatio(0,axis === 'upper' ? size.height : size.width,axis === 'upper' ? 160 : 260))} aria-valuemax={Math.floor(clampRatio(100,axis === 'upper' ? size.height : size.width,axis === 'upper' ? 160 : 260))} aria-valuenow={Math.round(ratios[axis])}
    onKeyDown={event => {
      const negative = axis === 'upper' ? 'ArrowUp' : 'ArrowLeft', positive = axis === 'upper' ? 'ArrowDown' : 'ArrowRight';
      if (event.key === negative || event.key === positive) {event.preventDefault(); changeRatio(axis, ratios[axis] + (event.key === negative ? -1 : 1) * (event.shiftKey ? 10 : 2));}
      if (event.key === 'Home' || event.key === 'End') {event.preventDefault(); changeRatio(axis, event.key === 'Home' ? 0 : 100);}
    }} onPointerDown={event => {event.preventDefault(); event.currentTarget.focus(); event.currentTarget.setPointerCapture(event.pointerId);}}
    onPointerMove={event => {
      if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
      const rect = (axis === 'upper' ? root : lower).current!.getBoundingClientRect();
      changeRatio(axis, (axis === 'upper' ? (event.clientY - rect.top) / rect.height : (event.clientX - rect.left) / rect.width) * 100);
    }} onPointerUp={event => {if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);}}/>;
  const pane = (key: string, value: Pane, hidden = false) => <section className="panel operational-pane" data-operational-pane={key}
    data-pane-id={key} data-pane-active={current === key} id={id + key} aria-labelledby={id + key + '-title'} tabIndex={0} hidden={hidden}
    onFocusCapture={() => setActive(key)} onPointerDownCapture={() => setActive(key)}>
    <header className="operational-pane-header"><h2 id={id + key + '-title'}><ConsoleCue kind="section"/>{value.title}</h2>{value.actions}</header>
    <div className="panel-body" data-pane-body data-scroll-owner="y">{value.content}</div>
  </section>;
  return <div ref={root} className="operational-layout" data-composition={split ? 'split' : 'switcher'} data-inspector={!!details}
    style={{'--soma-upper-share': ratios.upper + 'fr', '--soma-lower-share': (100 - ratios.upper) + 'fr', '--soma-left-share': ratios.left + 'fr', '--soma-right-share': (100 - ratios.left) + 'fr', '--soma-left-width': ratios.left + '%'} as CSSProperties}>
    {details && <div className="operational-layout-controls"><div role="group" aria-label="Operational pane" hidden={split}>
      {available.map(key => <button key={key} aria-controls={id + key} aria-pressed={current === key} onClick={() => {setActive(key); requestAnimationFrame(() => root.current?.querySelector<HTMLElement>(`[data-operational-pane="${key}"]`)?.focus());}}>{key === 'collection' ? 'Collection' : key === 'details' ? 'Details' : 'Context'}</button>)}
    </div><button className="soma-action action-quiet" onClick={() => {setRatios(defaultRatios); rememberRatios(sessionKey, defaultRatios);}}>Reset layout</button></div>}
    {pane('collection', collection, !split && current !== 'collection')}
    {details && <>{split && separator('upper')}<div ref={lower} className="operational-lower" data-context={!!context} hidden={!split && current === 'collection'}>
      {pane('details', details, !split && current !== 'details')}{context && <>{split && separator('left')}{pane('context', context, !split && current !== 'context')}</>}
    </div></>}
    <span className="sr-only" role="status">Active pane: {current}</span>
  </div>;
}
