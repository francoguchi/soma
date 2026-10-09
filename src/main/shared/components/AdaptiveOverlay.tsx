import type {ReactNode, RefObject} from 'react';
import {Modal} from './Modal';

/** Size changes preserve one modal, its isolation and both retained owner surfaces. */
export function AdaptiveOverlay({expanded, application, fallback, close, collapse, compact, manager}: {
  expanded: boolean; application: RefObject<HTMLElement | null>; fallback: () => HTMLElement | null;
  close: () => void; collapse: () => void; compact: ReactNode; manager: ReactNode;
}) {
  return <Modal title={expanded ? 'Reference Manager' : 'Settings'} application={application} fallback={fallback}
    close={close} closeLabel="Close Settings" className={'adaptive-overlay ' + (expanded ? 'overlay-expanded' : 'overlay-compact')}>
    {() => <>{expanded && <button type="button" onClick={collapse}>Return to Settings</button>}
      <div className="overlay-content" hidden={expanded}>{compact}</div>
      <div className="overlay-content" hidden={!expanded}>{manager}</div></>}
  </Modal>;
}
