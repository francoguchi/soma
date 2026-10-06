import {useRef, type RefObject} from 'react';
import {ConsoleCue} from '../../shared/components/ConsoleCue';
import {SectionTabs} from '../../shared/components/Section';
import {Profile} from './profile/Profile';
import {Preferences} from './Preferences';
import {ReferenceSurface} from '../reference/ReferenceSurface';
import {WorkingSurface} from '../../shared/interactions/use-working-intent';

export function Settings({path, navigate, application}: {path: string; navigate: (path: string) => void; application: RefObject<HTMLElement | null>}) {
  const references = path.startsWith('/settings/reference-data');
  const preferences = path === '/settings/preferences';
  const referencePath = useRef('/settings/reference-data'), visited = useRef(false);
  if (references) {referencePath.current = path; visited.current = true;}
  return <div className="operational-surface"><h1><ConsoleCue kind="command"/>Settings</h1><SectionTabs label="Settings sections" current={references ? '/settings/reference-data' : preferences ? '/settings/preferences' : '/settings/profile'} navigate={navigate} items={[{href: '/settings/profile', title: 'Profile'}, {href: '/settings/preferences', title: 'Preferences'}, {href: '/settings/reference-data', title: 'Reference data'}]}/>
    {visited.current && <WorkingSurface active={references}><div className="operational-surface" hidden={!references}><ReferenceSurface path={referencePath.current} navigate={navigate} application={application}/></div></WorkingSurface>}
    {!references && (preferences ? <Preferences application={application}/> : <Profile application={application}/>)}
  </div>;
}
