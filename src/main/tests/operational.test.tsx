import {afterEach, expect, test, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {OperationalLayout} from '../shared/components/OperationalLayout';
import {clampRatio, readRatios, rememberRatios} from '../shared/interactions/panel-ratios';

afterEach(() => {cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();});
function measurement() {
  vi.stubGlobal('ResizeObserver', class {observe() {} disconnect() {}});
  vi.spyOn(HTMLElement.prototype,'getBoundingClientRect').mockReturnValue({width:1000,height:700,x:0,y:0,top:0,left:0,right:1000,bottom:700,toJSON:()=>({})});
}
test('unselected layout has no lower regions or resize controls; creation has no Context', () => {
  measurement();const collection={title:'Records',content:<input aria-label="Retained query" defaultValue="Exact"/>};
  const {rerender}=render(<OperationalLayout sessionKey="test-create" collection={collection}/>);
  expect(screen.queryByRole('separator')).toBeNull();expect(screen.queryByRole('region',{name:'Details'})).toBeNull();
  const input=screen.getByLabelText('Retained query');
  rerender(<OperationalLayout sessionKey="test-create" collection={collection} details={{title:'Creating',content:<input aria-label="New name"/>}}/>);
  expect(screen.queryByRole('region',{name:'Context'})).toBeNull();expect(screen.getAllByRole('separator')).toHaveLength(1);
  expect(screen.getByLabelText('Retained query')).toBe(input);
});
test('keyboard resize, reset and session isolation change presentation only', () => {
  measurement();render(<OperationalLayout sessionKey="test-size" collection={{title:'Records',content:'list'}} details={{title:'Details',content:'truth'}} context={{title:'Context',content:'evidence'}}/>);
  const horizontal=screen.getByRole('separator',{name:'Collection and inspector size'});
  fireEvent.keyDown(horizontal,{key:'ArrowDown',shiftKey:true});expect(horizontal.getAttribute('aria-valuenow')).toBe('50');
  expect(readRatios('test-size').upper).toBe(50);expect(readRatios('other-key').upper).toBe(40);
  fireEvent.click(screen.getByRole('button',{name:'Reset layout'}));expect(readRatios('test-size').upper).toBe(40);
  expect(screen.getByText('truth')).toBeTruthy();expect(screen.getByText('evidence')).toBeTruthy();
});
test('minimum clamp is bounded and ratios are retained independently', () => {
  expect(clampRatio(-100,800,160)).toBe(25);expect(clampRatio(200,800,160)).toBe(75);
  expect(clampRatio(20,720,260)).toBeCloseTo(36.111,2);
  rememberRatios('a',{upper:50,left:60});rememberRatios('b',{upper:35,left:45});expect(readRatios('a').left).toBe(60);expect(readRatios('b').upper).toBe(35);
});
