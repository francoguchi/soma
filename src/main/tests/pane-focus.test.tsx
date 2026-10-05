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
  expect(screen.getByRole('region', {name: 'Evidence'}).querySelector('[data-pane-body]')).toBeTruthy();
  expect(screen.getByRole('heading', {name: 'Evidence'}).textContent).toBe('Evidence');
  rerender(<ConsolePanes panes={[panes[0]!]}/>);
  const work = screen.getByRole('region', {name: 'Work'});
  expect(work.dataset['paneActive']).toBe('true');
  expect(document.activeElement).toBe(work);
});

test('retained inactive panes keep their input while focus and narrow controls follow available panes', () => {
  vi.stubGlobal('matchMedia', () => ({matches: false, addEventListener: () => {}, removeEventListener: () => {}}));
  const records = {id: 'records', title: 'Records', content: <input aria-label="Collection filter" defaultValue=""/>};
  const work = {id: 'work', title: 'Create', content: <input aria-label="New name"/>};
  const {rerender} = render(<ConsolePanes panes={[records]} layout="single"/>);
  const filter = screen.getByLabelText('Collection filter') as HTMLInputElement;
  fireEvent.change(filter, {target: {value: 'Retained query'}});
  rerender(<ConsolePanes panes={[{...records, hidden: true}, work]} layout="form"/>);
  expect(screen.queryByRole('region', {name: 'Records'})).toBeNull();
  expect(screen.getByRole('region', {name: 'Create'}).dataset['paneActive']).toBe('true');
  expect(screen.queryByRole('button', {name: 'Records'})).toBeNull();
  expect(document.activeElement).toBe(screen.getByRole('region', {name: 'Create'}));
  rerender(<ConsolePanes panes={[records]} layout="single"/>);
  expect(screen.getByLabelText('Collection filter')).toBe(filter);
  expect(filter.value).toBe('Retained query');
  expect(document.activeElement).toBe(screen.getByRole('region', {name: 'Records'}));
});
