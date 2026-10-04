import {useState, type RefObject} from 'react';

// Logical pane activation never selects a record or steals focus from a control.
export function usePaneFocus(root: RefObject<HTMLElement | null>, initial: string) {
  const [active, setActive] = useState(initial);
  const activateFrom = (target: EventTarget) => {
    if (!(target instanceof Element) || target.closest('[aria-modal="true"]')) return;
    const pane = target.closest<HTMLElement>('[data-pane-id]');
    if (pane && root.current?.contains(pane) && !pane.hidden) setActive(pane.dataset['paneId']!);
  };
  const pointerActivate = (target: EventTarget) => {
    activateFrom(target);
    if (!(target instanceof Element)) return;
    // Composite widgets own focus (notably autocomplete pointer-down keeps
    // its input focused until the option's click accepts the value).
    if (target.closest('button,input,textarea,select,a,summary,label,[role],[contenteditable="true"]')) return;
    const focusable = target.closest('[tabindex]');
    if (focusable && !focusable.matches('[data-pane-id]')) return;
    const pane = target.closest<HTMLElement>('[data-pane-id]');
    if (pane && root.current?.contains(pane) && !target.closest('[aria-modal="true"]')) pane.focus({preventScroll: true});
  };
  const focusActive = () => root.current?.querySelector<HTMLElement>(`[data-pane-id="${active}"]:not([hidden])`)?.focus();
  return {active, activate: setActive, activateFrom, pointerActivate, focusActive};
}
