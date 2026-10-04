export class NavigationGuard {
  private pending: (() => void) | null = null;
  request(currentFlow: string, nextFlow: string, dirty: boolean, navigate: () => void): boolean {
    if (!dirty || currentFlow === nextFlow) {this.pending = null; navigate(); return true;}
    this.pending = navigate; return false;
  }
  stay() {this.pending = null;}
  abandon() {const navigate = this.pending; this.pending = null; navigate?.();}
}
export function warnBeforeUnload(dirty: () => boolean): () => void {
  const handler = (event: BeforeUnloadEvent) => {if (dirty()) {event.preventDefault(); event.returnValue = '';}};
  addEventListener('beforeunload', handler); return () => removeEventListener('beforeunload', handler);
}
