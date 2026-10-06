import {useLayoutEffect, useRef, useState, type ReactNode} from 'react';
import {createPortal} from 'react-dom';
/** Retain a collection's model/DOM when its ordinary and inspection hosts change.
 * A missing host detaches presentation, without discarding filters/pages/selection. */
export function RetainedContent({host, children, restoreFocus = false}: {host: HTMLElement | null; children: ReactNode; restoreFocus?: boolean}) {
  const [container] = useState(() => document.createElement('div'));
  const focused = useRef<HTMLElement | null>(null);
  const scroll = useRef(new Map<HTMLElement, {top: number; left: number}>());
  useLayoutEffect(() => {
    if (host) {
      host.append(container);
      for (const [node, position] of scroll.current) {node.scrollTop = position.top; node.scrollLeft = position.left;}
      if (restoreFocus && focused.current && container.contains(focused.current)) focused.current.focus({preventScroll: true});
    } else container.remove();
    return () => {container.remove();};
  }, [host, container, restoreFocus]);
  return createPortal(<div data-retained-content onFocusCapture={event => {if (event.target instanceof HTMLElement) focused.current = event.target;}} onScrollCapture={event => {
    const node = event.target;
    if (node instanceof HTMLElement && container.isConnected) scroll.current.set(node, {top: node.scrollTop, left: node.scrollLeft});
  }}>{children}</div>, container);
}
