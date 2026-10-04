export type ConsoleCueKind = 'command' | 'section' | 'subsection';

export function ConsoleCue({kind}: {kind: ConsoleCueKind}) {
  return <span className="console-cue" data-console-cue={kind} aria-hidden="true"/>;
}
