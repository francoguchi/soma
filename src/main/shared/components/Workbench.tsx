import {useLayoutEffect, useRef, useState, type ReactNode} from 'react';
import {usePaneFocus} from '../interactions/pane-focus';
export function Workbench({work, context, dirty = false}: {work: ReactNode; context: ReactNode; dirty?: boolean}) {
  const root = useRef<HTMLDivElement>(null), workPane = useRef<HTMLElement>(null), contextPane = useRef<HTMLElement>(null);
  const [wide, setWide] = useState(false);
  const {active: pane, activate: setPane, activateFrom, pointerActivate} = usePaneFocus(root, 'work');
  const switcher = useRef<HTMLDivElement>(null), currentPane = useRef(pane);
  currentPane.current = pane;
  useLayoutEffect(() => {
    const update = () => {if (!root.current) return; const next = root.current.getBoundingClientRect().width >= 1040; if (!next) {if (contextPane.current?.contains(document.activeElement)) setPane('context'); else if (workPane.current?.contains(document.activeElement)) setPane('work');} else if (switcher.current?.contains(document.activeElement)) {(currentPane.current === 'context' ? contextPane.current : workPane.current)?.focus();} setWide(next);};
    update(); const observer = new ResizeObserver(update); if (root.current) observer.observe(root.current); return () => observer.disconnect();
  }, []);
  return <div ref={root} onPointerDown={event => pointerActivate(event.target)} onFocusCapture={event => activateFrom(event.target)} className="workbench" data-layout={wide ? 'split' : 'switcher'}>{dirty && <p role="status">Unsaved UI changes — recoverable intent, not accepted data.</p>}<div ref={switcher} role="group" aria-label="Workbench pane" hidden={wide}><button aria-pressed={pane === 'work'} onClick={() => setPane('work')}>Work</button><button aria-pressed={pane === 'context'} onClick={() => setPane('context')}>Context and evidence</button></div><div className="workbench-panes"><section ref={workPane} data-pane-id="work" data-pane-active={pane === 'work'} aria-label="Operational work" hidden={!wide && pane !== 'work'} data-scroll-owner="y" tabIndex={0}><span className="active-pane-label" aria-hidden="true">{pane === 'work' ? 'active' : ''}</span>{work}</section><section ref={contextPane} data-pane-id="context" data-pane-active={pane === 'context'} aria-label="Context and evidence" hidden={!wide && pane !== 'context'} data-scroll-owner="y" tabIndex={0}><span className="active-pane-label" aria-hidden="true">{pane === 'context' ? 'active' : ''}</span>{context}</section></div></div>;
}
