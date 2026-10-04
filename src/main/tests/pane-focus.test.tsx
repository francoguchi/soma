import {afterEach, expect, test, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {ConsolePanes} from '../shared/components/ConsolePanes';

afterEach(() => {cleanup(); vi.unstubAllGlobals();});
test('pane activation preserves composite widget focus and safely restores a removed pane', () => {
  vi.stubGlobal('matchMedia', () => ({matches: true, addEventListener: () => {}, removeEventListener: () => {}}));
  const choose = vi.fn();
  const panes = [
    {id: 'work', title: 'Work', content: <p>Owner work</p>},
    {id: 'evidence', title: 'Evidence', content: <><input aria-label="Find record"/><div role="option" onPointerDown={event => event.preventDefault()} onClick={choose}>Existing record</div></>},
  ];
  const {rerender} = render(<ConsolePanes panes={panes}/>);
  const input = screen.getByLabelText('Find record');
  fireEvent.focus(input); input.focus();
  fireEvent.pointerDown(screen.getByRole('option'));
  expect(document.activeElement).toBe(input);
  fireEvent.click(screen.getByRole('option'));
  expect(choose).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('region', {name: 'Evidence'}).dataset['paneActive']).toBe('true');
  expect(screen.getByRole('status').textContent).toContain('Active pane: Evidence');
  expect(document.querySelector('.active-pane-label')).toBeNull();
  rerender(<ConsolePanes panes={[panes[0]!]}/>);
  const work = screen.getByRole('region', {name: 'Work'});
  expect(work.dataset['paneActive']).toBe('true');
  expect(document.activeElement).toBe(work);
});
