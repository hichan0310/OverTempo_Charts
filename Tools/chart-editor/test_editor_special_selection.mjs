import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
const between=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
function fixture(){
 const context={state:{notes:[{id:1,timeMs:700,lane:0,durationMs:0},{id:2,timeMs:1600,lane:1,durationMs:0}],
  speedLimitLines:[{timeMs:1000,durationMs:500,maxSpeed:1.2,startMaxSpeed:1.8,label:'cap'}],
  stageDeltaLines:[{timeMs:3000,durationMs:0,speedDelta:-.13,label:'delta'}],selectedIds:new Set(),selectedSpecialId:null,
  meta:{},difficulty:{},encryption:{},autoCoef:{settings:{}},bpm:120,snapDiv:4,offsetMs:0},
 history:{undo:[],redo:[],max:150},nextId:3,updatePanels(){},updateUndoRedoButtons(){},syncStateToUi(){},
 autoCoefSyncSettingsToUi(){},autoCoefUpdateStats(){},sortTimelineEvents(){},
 laneArea:()=>({left:100,right:500}),msToY:t=>1000-t*.2,yToMs:y=>(1000-y)/.2,
 snapTime:t=>Math.round(t/100)*100,snapMs:()=>100,Math,Number,Set,JSON,
 $:()=>({disabled:false}),document:{activeElement:null}};
 vm.createContext(context);
 vm.runInContext(between('// Special-note canvas editing.','// End special-note canvas editing.'),context);
 vm.runInContext(between('function snapshot()','function normalizedBpmChanges()'),context);
 vm.runInContext(between('function sortNotes()','function selectedNotes()'),context);
 return context;
}
const pointer={button:0,preventDefault(){}};
{
 const c=fixture(),entry=c.specialEntries()[0];
 assert.equal(c.hitSpecialAt(300,c.msToY(1250)).handle,'move');
 assert.equal(c.hitSpecialAt(106,c.msToY(1000)).handle,'start');
 assert.equal(c.hitSpecialAt(488,c.msToY(1500)).handle,'end');
 assert.equal(c.hitSpecialAt(90,c.msToY(1250)),null);
 c.beginSpecialDrag(pointer,{x:488,y:c.msToY(1500)});
 c.moveSpecialDrag({x:488,y:c.msToY(2000)});
 assert.equal(entry.line.durationMs,1000);
 assert.equal(c.state.notes.length,2,'normal notes must remain intact during the drag preview');
 c.finishSpecialDrag();assert.equal(c.state.notes.length,2);
 assert.equal(c.history.undo.length,1,'drag is one undo transaction');
 assert.equal(entry.line.maxSpeed,1.2);assert.equal(entry.line.startMaxSpeed,1.8);assert.equal(entry.line.label,'cap');
 c.undo();assert.equal(c.state.notes.length,2);assert.equal(c.state.speedLimitLines[0].durationMs,500);
 c.redo();assert.equal(c.state.notes.length,2);assert.equal(c.state.speedLimitLines[0].durationMs,1000);
}
{
 const c=fixture(),entry=c.specialEntries()[1];
 c.beginSpecialDrag(pointer,{x:488,y:c.msToY(3000)});
 c.moveSpecialDrag({x:488,y:c.msToY(3500)});c.finishSpecialDrag();
 assert.equal(entry.line.durationMs,500,'tap endpoint grows a hold');
 c.beginSpecialDrag(pointer,{x:106,y:c.msToY(3000)});
 c.moveSpecialDrag({x:106,y:c.msToY(3100)});c.finishSpecialDrag();
 assert.equal(entry.line.timeMs,3100);assert.equal(entry.line.durationMs,400);
 c.beginSpecialDrag(pointer,{x:300,y:c.msToY(3300)});
 c.moveSpecialDrag({x:300,y:c.msToY(4300)});c.finishSpecialDrag();
 assert.equal(entry.line.timeMs,4100);assert.equal(entry.line.durationMs,400);assert.equal(entry.line.speedDelta,-.13);
 assert.equal(c.deleteSelectedSpecial(),true);assert.equal(c.state.stageDeltaLines.length,0);
 c.undo();assert.equal(c.state.stageDeltaLines.length,1);assert.equal(c.state.stageDeltaLines[0].timeMs,4100);
}
{
 const c=fixture();c.beginSpecialDrag(pointer,{x:300,y:c.msToY(1250)});c.finishSpecialDrag();
 assert.equal(c.history.undo.length,0,'selecting without editing is not a history entry');
 c.beginSpecialDrag(pointer,{x:488,y:c.msToY(1500)});
 c.moveSpecialDrag({x:488,y:c.msToY(900)});c.finishSpecialDrag();
 assert.equal(c.state.speedLimitLines[0].durationMs,0,'shortening past head produces a tap, never negative duration');
}
console.log('Special canvas editing passed: hit testing, both endpoints, tap-to-hold, move, effects preserved, overlap preservation, single-step undo/redo and delete.');

{
 const c=fixture();
 const tap=c.addNote({timeMs:1000,lane:2,durationMs:0});
 const hold=c.addNote({timeMs:1200,lane:3,durationMs:600});
 assert.ok(tap&&hold,'place regular taps and holds over a special interval');
 assert.equal(c.noteConflictsWithList({timeMs:1300,lane:0,durationMs:0},c.state.notes),null);
 assert.equal(c.noteConflictsWithList({timeMs:1300,lane:3,durationMs:0},c.state.notes).id,hold.id,'ordinary lane conflict still detected');
}
