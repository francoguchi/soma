type Axis = 'x' | 'y';
export function scrollOwner(origin: Element | null, axis: Axis): HTMLElement | null {
  for (let node = origin; node; node = node.parentElement) {
    if (!(node instanceof HTMLElement)) continue;
    const declared = node.dataset['scrollOwner'];
    if ((declared === axis || declared === 'both') && (axis === 'x' ? node.scrollWidth > node.clientWidth : node.scrollHeight > node.clientHeight)) return node;
  }
  return null;
}
export function installScrollOwnership(root: HTMLElement, primary: () => HTMLElement | null): () => void {
  const gesture = () => dispatchEvent(new Event('soma-scroll-gesture'));
  const apply = (owner: HTMLElement, axis: Axis, delta: number) => {if (axis === 'x') owner.scrollLeft += delta; else owner.scrollTop += delta;};
  const wheel = (event: WheelEvent) => {
    if (event.ctrlKey) return; // browser zoom is not application scrolling
    const axis = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? 'x' : 'y';
    const owner = scrollOwner(event.target instanceof Element ? event.target : null, axis);
    gesture();
    if (!owner) return;
    event.preventDefault();
    const delta = axis === 'x' ? event.deltaX : event.deltaY;
    apply(owner, axis, delta * (event.deltaMode === 1 ? 20 : event.deltaMode === 2 ? owner.clientHeight : 1));
  };
  const keyboard = (event: KeyboardEvent) => {
    if (event.defaultPrevented || event.ctrlKey || event.altKey || event.metaKey || !['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'PageDown', 'PageUp', 'Home', 'End', ' '].includes(event.key)) return;
    const target = event.target instanceof Element ? event.target : null;
    if (target?.closest('input,textarea,select,button,a,[contenteditable="true"],[role="combobox"]')) return;
    const axis = event.key === 'ArrowLeft' || event.key === 'ArrowRight' ? 'x' : 'y';
    const owner = scrollOwner(document.activeElement, axis) ?? (axis === 'y' ? primary() : null);
    if (!owner || (axis === 'y' ? owner.scrollHeight <= owner.clientHeight : owner.scrollWidth <= owner.clientWidth)) return;
    event.preventDefault(); gesture();
    const delta = event.key === 'Home' ? -owner.scrollHeight : event.key === 'End' ? owner.scrollHeight : event.key === 'ArrowDown' || event.key === 'ArrowRight' ? 40 : event.key === 'ArrowUp' || event.key === 'ArrowLeft' ? -40 : (event.key === 'PageUp' || event.shiftKey ? -1 : 1) * owner.clientHeight * 0.8;
    apply(owner, axis, delta);
  };
  let touch: {x: number; y: number; lastX: number; lastY: number; origin: Element | null; axis: Axis | null; owner: HTMLElement | null} | null = null;
  const start = (event: TouchEvent) => {const point = event.touches[0]; touch = point ? {x: point.clientX, y: point.clientY, lastX: point.clientX, lastY: point.clientY, origin: event.target instanceof Element ? event.target : null, axis: null, owner: null} : null;};
  const move = (event: TouchEvent) => {
    const point = event.touches[0]; if (!point || !touch || event.touches.length !== 1) {touch = null; return;}
    if (!touch.axis && Math.hypot(point.clientX - touch.x, point.clientY - touch.y) >= 5) {
      touch.axis = Math.abs(point.clientX - touch.x) > Math.abs(point.clientY - touch.y) ? 'x' : 'y'; touch.owner = scrollOwner(touch.origin, touch.axis); gesture();
    }
    if (touch.axis && touch.owner) {event.preventDefault(); apply(touch.owner, touch.axis, touch.axis === 'x' ? touch.lastX - point.clientX : touch.lastY - point.clientY);}
    touch.lastX = point.clientX; touch.lastY = point.clientY;
  };
  const end = () => {touch = null;};
  root.addEventListener('wheel', wheel, {passive: false}); root.addEventListener('keydown', keyboard);
  root.addEventListener('touchstart', start, {passive: true}); root.addEventListener('touchmove', move, {passive: false}); root.addEventListener('touchend', end); root.addEventListener('touchcancel', end);
  return () => {root.removeEventListener('wheel', wheel); root.removeEventListener('keydown', keyboard); root.removeEventListener('touchstart', start); root.removeEventListener('touchmove', move); root.removeEventListener('touchend', end); root.removeEventListener('touchcancel', end);};
}
