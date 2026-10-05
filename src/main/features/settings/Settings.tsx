import {useRef, type RefObject} from 'react';
import {ConsoleCue} from '../../shared/components/ConsoleCue';
import {ConsolePanes} from '../../shared/components/ConsolePanes';
import {Profile} from './profile/Profile';
import {Preferences} from './Preferences';
import {ReferenceSurface} from '../reference/ReferenceSurface';
import {WorkingSurface} from '../../shared/interactions/use-working-intent';

export function Settings({path, navigate, application}: {path: string; navigate: (path: string) => void; application: RefObject<HTMLElement | null>}) {
  const references = path.startsWith('/settings/reference-data');
  const preferences = path === '/settings/preferences';
  const referencePath = useRef('/settings/reference-data'), visited = useRef(false);
  if (references) {referencePath.current = path; visited.current = true;}
  return <div className="operational-surface"><h1><ConsoleCue kind="command"/>Settings{references ? ' / Reference data' : preferences ? ' / Preferences' : ' / Profile'}</h1><div className="action-strip" role="group" aria-label="Settings sections"><button aria-pressed={!references && !preferences} onClick={() => navigate('/settings/profile')}>Profile</button><button aria-pressed={preferences} onClick={() => navigate('/settings/preferences')}>Preferences</button><button aria-pressed={references} onClick={() => navigate('/settings/reference-data')}>Reference data</button></div>
    {visited.current && <WorkingSurface active={references}><div className="operational-surface" hidden={!references}><ReferenceSurface path={referencePath.current} navigate={navigate} application={application}/></div></WorkingSurface>}
    {!references && <ConsolePanes label="Settings pane" layout="form" panes={[
      {id: 'settings', title: preferences ? 'Preferences' : 'Profile', content: preferences ? <Preferences application={application}/> : <Profile application={application}/>},
    ]}/>}
  </div>;
}
