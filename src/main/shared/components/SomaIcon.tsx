import type {SVGProps} from 'react';
const shapes = {
  profile: 'M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6M2 15v-2c0-4 12-4 12 0v2',
  preferences: 'M2 4h12M2 12h12M5 2v4M11 10v4',
  reference: 'M2 4c0-3 12-3 12 0v8c0 3-12 3-12 0V4M2 4c0 3 12 3 12 0M2 8c0 3 12 3 12 0',
  customer: 'M2 15V3h8v12M10 7h4v8M5 6h2M5 9h2M5 12h2M1 15h14',
  contact: 'M6 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4M2 13c0-5 8-5 8 0M12 4h3M12 8h3M12 12h3',
  dispatch: 'M8 15s5-6 5-9a5 5 0 0 0-10 0c0 3 5 9 5 9M8 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4',
  add: 'M8 2v12M2 8h12', refresh: 'M13 5a5.5 5.5 0 1 0 0 6M13 1v4H9',
  search: 'M7 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M10 10l5 5',
  history: 'M2 5a6 6 0 1 1-1 5M2 1v4h4M8 4v4l3 2',
  identity: 'M1 3h14v10H1zM5 8a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3M3 11c0-3 4-3 4 0M10 6h3M10 10h3',
  lifecycle: 'M3 3h10v10H3zM5 8l2 2 4-4',
  email: 'M1 3h14v10H1zM1 3l7 6 7-6',
  affiliation: 'M6 10l4-4M6 6l-2 2a3 3 0 0 0 4 4l2-2M10 10l2-2a3 3 0 0 0-4-4L6 6',
  evidence: 'M3 1h7l3 3v11H3zM10 1v4h3M5 8h6M5 11h6',
  back: 'M7 3L2 8l5 5M2 8h12', open: 'M6 3l5 5-5 5',
} as const;
export type IconName = keyof typeof shapes;
/** Repository-owned functional icons. Accessible names belong to the surrounding label/action. */
export function SomaIcon({name, ...props}: {name: IconName} & SVGProps<SVGSVGElement>) {
  return <svg {...props} className={'soma-icon ' + (props.className ?? '')} data-icon={name} width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={shapes[name]}/></svg>;
}
