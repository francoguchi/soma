import {useLayoutEffect, useRef, useState, type ReactNode} from 'react';
import {usePaneFocus} from '../interactions/pane-focus';

export function ConsolePanes({panes}: {panes: readonly {id: string; title: string; content: ReactNode}[]}) {
  const [wide, setWide] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const {active, activate, activateFrom, pointerActivate} = usePaneFocus(root, panes[0]!.id);
  const selection = useRef(active);
  const fallbackPending = useRef(false);
  selection.current = active;
  useLayoutEffect(() => {
    if (!panes.some(pane => pane.id === active) && panes[0]) {
      fallbackPending.current = true;
      activate(panes[0].id);
    } else if (fallbackPending.current) {
      fallbackPending.current = false;
      root.current?.querySelector<HTMLElement>(`[data-pane-id="${active}"]`)?.focus();
    }
  }, [panes, active, activate]);
  useLayoutEffect(() => {
    const media = matchMedia('(min-width: 1040px)');
    const update = () => {
      const active = document.activeElement;
      const focused = Array.from(root.current?.querySelectorAll<HTMLElement>('[data-console-pane]') ?? []).find(pane => pane.contains(active));
      if (!media.matches && focused) activate(focused.dataset['consolePane']!);
      if (media.matches && active?.closest('.pane-switcher')) root.current?.querySelector<HTMLElement>(`[data-console-pane="${selection.current}"]`)?.focus();
      setWide(media.matches);
    };
    update(); media.addEventListener('change', update); return () => media.removeEventListener('change', update);
  }, []);
  return <div ref={root} className="operational-console" data-layout={wide ? 'split' : 'switcher'} onPointerDown={event => pointerActivate(event.target)} onFocusCapture={event => activateFrom(event.target)}>
    <div className="pane-switcher" role="group" aria-label="Diagnostics pane" hidden={wide}>
      {panes.map(pane => <button key={pane.id} aria-pressed={active === pane.id} aria-controls={`console-${pane.id}`} onClick={() => activate(pane.id)}>{pane.title}</button>)}
    </div>
    <p className="sr-only" role="status">Active pane: {panes.find(pane => pane.id === active)?.title}</p>
    <div className="diagnostics-grid">{panes.map(pane => <section key={pane.id} id={`console-${pane.id}`} data-console-pane={pane.id} data-pane-id={pane.id} data-pane-active={pane.id === active} data-scroll-owner="y" className="panel" tabIndex={0} aria-labelledby={`console-title-${pane.id}`} hidden={!wide && pane.id !== active}><h2 id={`console-title-${pane.id}`}>{pane.title}<span className="active-pane-label" aria-hidden="true">{pane.id === active ? 'active' : ''}</span></h2>{pane.content}</section>)}</div>
  </div>;
}
