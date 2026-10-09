import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {chromium,expect} from '@playwright/test';
const origin=process.argv[2];assert.match(origin,/^http:\/\/127\.0\.0\.1:[1-9][0-9]*$/u);
const output='../../.tmp/operational-ui';await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
 const context=await browser.newContext({viewport:{width:1440,height:900},hasTouch:true});const page=await context.newPage();const errors=[];
 page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>assert.equal(new URL(request.url()).origin,origin));
 await page.goto(origin+'/test/operational.html');await expect(page.locator('.status-readiness')).toHaveText('READY');
 const main=page.locator('.operational-main'), layout=main.locator('.operational-layout'), collection=main.locator('[data-operational-pane=collection]');
 const row=i=>collection.getByRole('row').filter({has:page.getByText('Synthetic record '+i,{exact:true})});
 const capture=async name=>{await page.screenshot({path:output+'/'+name+'.png',fullPage:true});};
 const geometry=async()=>{
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const footer=await page.locator('.operational-footer').boundingBox();assert(footer);assert(footer.y+footer.height<=await page.evaluate(()=>innerHeight)+1);
   for(const pane of await page.locator('[data-operational-pane]:visible').all()) {const box=await pane.boundingBox();assert(box&&box.width>200&&box.height>100);}
 };
 await expect(page.getByRole('navigation',{name:'Workspaces'}).getByRole('button')).toHaveCount(5);
 await expect(page.getByRole('button',{name:'Tickets',exact:true})).toBeDisabled();
 await expect(main.getByRole('separator')).toHaveCount(0);await expect(main.getByRole('region',{name:'Details'})).toHaveCount(0);
 await capture('1440-browse');await row(0).getByText('Synthetic record 0',{exact:true}).click();
 const details=main.locator('[data-operational-pane=details]'), evidence=main.locator('[data-operational-pane=context]');
 await expect(details).toContainText('Synthetic accepted record');await expect(details.getByRole('textbox')).toHaveCount(0);
 await expect(main.getByRole('separator')).toHaveCount(2);await capture('1440-selected');
 await row(0).press('ArrowDown');await expect(row(1)).toBeFocused();await expect(row(0)).toHaveAttribute('aria-selected','true');
 await row(1).press('Enter');await expect(details).toBeFocused();await expect(details).toContainText('Synthetic record 1');
 await page.getByRole('button',{name:'Edit selected record',exact:true}).click();await page.getByRole('textbox',{name:'Record name',exact:true}).fill('Dirty retained fixture');
 await expect(page.getByRole('status').filter({hasText:'Recovery: checkpointed'})).toBeVisible({timeout:10000});
 await row(0).getByText('Synthetic record 0',{exact:true}).click();await expect(page.getByRole('dialog',{name:'Leave unsaved changes?'})).toBeVisible();
 await page.getByRole('dialog').getByRole('button',{name:'Cancel',exact:true}).click();await expect(page.getByRole('textbox',{name:'Record name',exact:true})).toHaveValue('Dirty retained fixture');
 await page.reload();await expect(page.locator('.status-readiness')).toHaveText('READY');await row(1).getByText('Synthetic record 1',{exact:true}).click();await main.getByRole('button',{name:'Edit selected record',exact:true}).click();
 await main.getByRole('button',{name:'Restore intent',exact:true}).click();await expect(main.getByRole('textbox',{name:'Record name',exact:true})).toHaveValue('Dirty retained fixture');
 await capture('1440-edit');
 // Overlay over dirty background: same dialog expands, background remains inert/mounted.
 const settings=page.getByRole('button',{name:'Settings',exact:true});await settings.click();const dialog=page.getByRole('dialog');
 await expect(dialog).toHaveAccessibleName('Settings');await expect(dialog.getByRole('button',{name:'Close Settings'})).toBeFocused();
 await dialog.getByRole('button',{name:'Close Settings'}).press('Tab');await expect(dialog.getByRole('textbox',{name:'Display name'})).toBeFocused();
 await dialog.getByRole('textbox',{name:'Display name'}).press('Shift+Tab');await expect(dialog.getByRole('button',{name:'Close Settings'})).toBeFocused();
 assert(await page.locator('.operational-frame').evaluate(node=>node.inert));const dialogIdentity=await dialog.evaluate(node=>{node.dataset.identity='same';return node.dataset.identity;});
 await capture('1440-settings-compact');await dialog.getByRole('button',{name:'Reference data',exact:true}).click();
 await expect(dialog).toHaveAccessibleName('Reference Manager');assert.equal(await dialog.getAttribute('data-identity'),dialogIdentity);await expect(page.getByRole('dialog')).toHaveCount(1);
 await capture('1440-settings-expanded-browse');
 await dialog.getByText('Synthetic record 0',{exact:true}).click();await capture('1440-settings-expanded-selected');
 await dialog.getByRole('button',{name:'Edit selected record',exact:true}).click();await dialog.getByRole('textbox',{name:'Record name',exact:true}).fill('Overlay dirty');
 await dialog.getByRole('button',{name:'Return to Settings',exact:true}).click();await expect(page.getByRole('dialog',{name:'Leave unsaved changes?'})).toBeVisible();
 await expect(page.getByRole('dialog',{name:'Leave unsaved changes?'}).getByRole('button',{name:'Cancel',exact:true})).toBeFocused();assert.deepEqual(errors,[]);
 await page.getByRole('dialog',{name:'Leave unsaved changes?'}).getByRole('button',{name:'Cancel',exact:true}).click();await expect(dialog.getByRole('textbox',{name:'Record name',exact:true})).toHaveValue('Overlay dirty');
 await dialog.getByRole('button',{name:'Cancel edit',exact:true}).click();await page.getByRole('dialog',{name:'Leave unsaved changes?'}).getByRole('button',{name:'Leave without saving',exact:true}).click();
 await dialog.getByRole('button',{name:'Return to Settings',exact:true}).click();await expect(dialog).toHaveAccessibleName('Settings');await dialog.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(settings).toBeFocused();
 await expect(page.getByRole('textbox',{name:'Record name',exact:true})).toHaveValue('Dirty retained fixture');
 // Dirty cancellation is guarded, Save accepts only synthetic state.
 await main.getByRole('button',{name:'Cancel edit',exact:true}).click();await expect(page.getByRole('dialog',{name:'Leave unsaved changes?'})).toBeVisible();await page.getByRole('dialog').getByRole('button',{name:'Cancel',exact:true}).click();
 await main.getByRole('button',{name:'Save',exact:true}).click();await expect(details).toContainText('Dirty retained fixture');await expect(details.getByRole('textbox')).toHaveCount(0);
 const horizontal=main.getByRole('separator',{name:'Collection and inspector size'}),vertical=main.getByRole('separator',{name:'Details and Context size'});
 await horizontal.focus();await horizontal.press('Shift+ArrowDown');await expect(horizontal).toHaveAttribute('aria-valuenow','50');
 await vertical.focus();await vertical.press('ArrowRight');await expect(vertical).toHaveAttribute('aria-valuenow','52');
 await vertical.press('End');assert(Number(await vertical.getAttribute('aria-valuenow'))<=Number(await vertical.getAttribute('aria-valuemax')));await main.getByRole('button',{name:'Reset layout'}).click();
 await horizontal.press('Shift+ArrowDown');await vertical.press('ArrowRight');
 const b=await horizontal.boundingBox();await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width/2,b.y+55);await page.mouse.up();assert(Number(await horizontal.getAttribute('aria-valuenow'))>50);
 const vb=await vertical.boundingBox();await page.mouse.move(vb.x+vb.width/2,vb.y+vb.height/2);await page.mouse.down();await page.mouse.move(vb.x+70,vb.y+vb.height/2);await page.mouse.up();assert(Number(await vertical.getAttribute('aria-valuenow'))>52);
 await expect(details).toContainText('Revision');await main.getByRole('button',{name:'Reset layout'}).click();await expect(horizontal).toHaveAttribute('aria-valuenow','40');await expect(vertical).toHaveAttribute('aria-valuenow','50');
 // New is lower-left only, Cancel never allocates identity; Save selects accepted synthetic result.
 await main.getByRole('button',{name:'New',exact:true}).click();await expect(main.getByRole('region',{name:'Creating'})).toBeVisible();await expect(main.getByRole('region',{name:'Context'})).toHaveCount(0);await expect(main.getByRole('separator')).toHaveCount(1);await capture('1440-creating');
 assert((await main.getByRole('region',{name:'Creating'}).boundingBox()).width<(await collection.boundingBox()).width*.6);
 await main.getByRole('button',{name:'Cancel edit',exact:true}).click();await expect(details).toContainText('Dirty retained fixture');
 await main.getByRole('button',{name:'New',exact:true}).click();await main.getByRole('textbox',{name:'Record name',exact:true}).fill('New synthetic identity');await main.getByRole('button',{name:'Save',exact:true}).click();await expect(details).toContainText('New synthetic identity');await expect(evidence).toBeVisible();
 // One-list exact query and ordinary return; stale query cannot overwrite later result.
 await page.getByRole('textbox',{name:'Exact synthetic name'}).fill('slow');await collection.getByRole('button',{name:'Search',exact:true}).click();await page.getByRole('textbox',{name:'Exact synthetic name'}).fill('Synthetic record 0');await collection.getByRole('button',{name:'Search',exact:true}).click();
 await expect(collection.getByRole('row')).toHaveCount(2);await page.waitForTimeout(250);await expect(collection.getByRole('row')).toHaveCount(2);
 await collection.getByRole('button',{name:'Clear search'}).click();await expect(collection.getByRole('row')).toHaveCount(101);
 await collection.getByRole('button',{name:'Next page'}).click();await expect(collection.getByText('Synthetic record 100',{exact:true})).toBeVisible();
 await page.getByRole('textbox',{name:'Exact synthetic name'}).fill('Synthetic record 0');await collection.getByRole('button',{name:'Search',exact:true}).click();await expect(collection.getByRole('row')).toHaveCount(2);
 await collection.getByRole('button',{name:'Clear search'}).click();await expect(collection.getByText('Synthetic record 100',{exact:true})).toBeVisible();
 await main.getByRole('button',{name:'Refresh',exact:true}).click();await expect(collection.getByText('Synthetic record 0',{exact:true})).toBeVisible();
 await collection.getByText('Synthetic record 0',{exact:true}).click();await evidence.getByRole('button',{name:'Evidence',exact:true}).click();
 const evidenceBody=evidence.locator('[data-pane-body]');await evidenceBody.evaluate(node=>node.scrollTop=100);const scroll=await evidenceBody.evaluate(node=>node.scrollTop);assert(scroll>0);
 await page.getByRole('button',{name:'Settings',exact:true}).click();await page.getByRole('dialog').press('Escape');assert.equal(await evidenceBody.evaluate(node=>node.scrollTop),scroll);
 // Real geometry captures. Actual measured minima, not an assumed 1040 split rule.
 for(const width of [1440,1040,1039,390]) {
   await page.setViewportSize({width,height:900});await geometry();
   const split=await layout.getAttribute('data-composition');
   if(split==='switcher') {await main.getByRole('button',{name:'Details',exact:true}).click();await expect(details).toBeVisible();await capture(width+'-details');await main.getByRole('button',{name:'Context',exact:true}).click();await expect(evidence).toBeVisible();await capture(width+'-context');await main.getByRole('button',{name:'Collection',exact:true}).click();}
   else {const c=await collection.boundingBox(),d=await details.boundingBox(),e=await evidence.boundingBox();assert(c.y<d.y&&Math.abs(d.y-e.y)<1&&d.x<e.x);}
   await capture(width+'-composition');
   await settings.click();await capture(width+'-compact');await page.getByRole('dialog').getByRole('button',{name:'Reference data',exact:true}).click();await capture(width+'-expanded');
   const manager=page.getByRole('dialog');await manager.getByText('Synthetic record 0',{exact:true}).click();
   if(await manager.locator('.operational-layout').getAttribute('data-composition')==='switcher') await manager.getByRole('button',{name:'Details',exact:true}).click();
   await expect(manager.getByRole('button',{name:'Edit selected record',exact:true})).toBeVisible();await capture(width+'-expanded-selected');
   await page.getByRole('dialog').press('Escape');
 }
 await page.setViewportSize({width:1440,height:480});await expect(layout).toHaveAttribute('data-composition','switcher');await main.getByRole('button',{name:'Details',exact:true}).click();await geometry();await capture('1440-constrained-height');
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({forcedColors:'active',reducedMotion:'reduce'});await main.getByRole('button',{name:'Details',exact:true}).click();await capture('390-forced-colors');
 await page.emulateMedia({forcedColors:'none'});await page.setViewportSize({width:1440,height:900});
 // Browser CSS zoom (not a screenshot scale); measured layout must recompose.
 await page.evaluate(()=>document.documentElement.style.zoom='2');await expect(layout).toHaveAttribute('data-composition','switcher');await main.getByRole('button',{name:'Details',exact:true}).click();await geometry();await capture('1440-200-percent-zoom');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth));
 await page.evaluate(()=>document.documentElement.style.zoom='1');await page.setViewportSize({width:1440,height:900});await expect(layout).toHaveAttribute('data-composition','split');
 await main.getByRole('button',{name:'Clear selection',exact:true}).click();await expect(main.getByRole('separator')).toHaveCount(0);await expect(main.getByRole('region',{name:'Context'})).toHaveCount(0);await geometry();
 assert.deepEqual(errors,[]);console.log('Phase B: interaction, recovery, same-overlay, resizing and responsive geometry passed. Screenshots: .tmp/operational-ui');
} finally {await browser.close();}
