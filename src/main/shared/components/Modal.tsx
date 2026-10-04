import {useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode, type RefObject} from 'react';
import {createPortal} from 'react-dom';
const focusable = 'button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]';
export function Modal({title, application, fallback, close, children, dismissible = true}: {title: string; application: RefObject<HTMLElement | null>; fallback: () => HTMLElement | null; close: () => void; children: (isolated: boolean) => ReactNode; dismissible?: boolean}) {
  const id = useId(), node = useRef<HTMLDivElement>(null), invoker = useRef(document.activeElement);
  const [isolated, setIsolated] = useState(false);
  useLayoutEffect(() => {
    const app = application.current, dialog = node.current;
    if (!app || !dialog || app.inert || !('inert' in app)) return;
    const previous = document.documentElement.style.overflow;
    app.inert = true; document.documentElement.style.overflow = 'hidden';
    setIsolated(app.inert && document.documentElement.style.overflow === 'hidden');
    (dialog.querySelector<HTMLElement>('[data-safe-focus]:not(:disabled)') ?? dialog).focus();
    const contain = (event: FocusEvent) => {if (!dialog.contains(event.target as Node)) dialog.querySelector<HTMLElement>('[data-safe-focus]')?.focus();};
    document.addEventListener('focusin', contain);
    const observer = new MutationObserver(() => {if (!app.inert || document.documentElement.style.overflow !== 'hidden') setIsolated(false);});
    observer.observe(app, {attributes: true, attributeFilter: ['inert']}); observer.observe(document.documentElement, {attributes: true, attributeFilter: ['style']});
    return () => {observer.disconnect(); document.removeEventListener('focusin', contain); app.inert = false; document.documentElement.style.overflow = previous;
      const target = invoker.current;
      if (target instanceof HTMLElement && target.isConnected && !target.closest('[inert]') && target.getClientRects().length) target.focus(); else fallback()?.focus();};
  }, [application]);
  useEffect(() => {if (isolated && !application.current?.inert) setIsolated(false);});
  const currentlyIsolated = () => !!application.current?.inert && document.documentElement.style.overflow === 'hidden';
  return createPortal(<div className="modal-backdrop"><div ref={node} role="dialog" aria-modal="true" aria-labelledby={id} tabIndex={-1} className="modal" data-scroll-owner="y" onClickCapture={event => {if (!currentlyIsolated() && !(event.target as Element).closest('[data-safe-focus]')) {event.preventDefault(); event.stopPropagation(); setIsolated(false);}}} onSubmitCapture={event => {if (!currentlyIsolated()) {event.preventDefault(); event.stopPropagation(); setIsolated(false);}}} onKeyDown={event => {
    if (event.key === 'Escape' && dismissible) {event.preventDefault(); event.stopPropagation(); close();}
    if (event.key !== 'Tab') return;
    const elements = Array.from(node.current?.querySelectorAll<HTMLElement>(focusable) ?? []).filter(element => element.getClientRects().length && !element.closest('[hidden]'));
    const first = elements[0], last = elements.at(-1);
    if (!first) {event.preventDefault(); node.current?.focus();}
    else if (event.shiftKey && (document.activeElement === first || document.activeElement === node.current)) {event.preventDefault(); last?.focus();}
    else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
  }}><h2 id={id}>{title}</h2>{!isolated && <p role="alert">Consequential actions are unavailable until dialog isolation is established.</p>}<fieldset disabled={!isolated}>{children(isolated)}</fieldset><button type="button" data-safe-focus onClick={close} disabled={!dismissible}>Cancel</button>{!dismissible && <p>This operation is atomic. Wait for its owner to finish before leaving.</p>}</div></div>, document.body);
}
