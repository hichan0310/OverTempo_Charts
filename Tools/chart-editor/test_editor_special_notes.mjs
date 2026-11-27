import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
// Parse the entire script as well as executing its import/export paths.
new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
function source(start,end){return html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));}
const context={state:{notes:[],meta:{},difficulty:{},selectedIds:new Set(),encryption:{},autoCoef:{settings:{}}},
  nextId:1,normalizedBpmChanges:()=>[],exportBpmChanges:()=>[],baseCoefFromNote:n=>n.speedupCoef??1,
  dedupeAndRemoveOverlapsKeepFirst:notes=>({notes,dropped:[]}),
  syncUiToState(){},enforceNoOverlap:()=>0,syncStateToUi(){},updatePanels(){},
  autoCoefSyncSettingsToUi(){},autoCoefUpdateStats(){},sortNotes(){},projectSelectedAudioName:()=>'',
  $:()=>({value:'',checked:false}),document:{getElementById:()=>null}};
vm.createContext(context);
vm.runInContext(source('function legacySpecialNotes(', 'function sortTimelineEvents()'),context);
vm.runInContext(source('function sortTimelineEvents()', 'function updateTimelineEventList()'),context);
vm.runInContext(source('function exportSpeedLimitLines()', 'function playHit('),context);
vm.runInContext(source('function projectImportChartData(', 'function projectBuildPayload()'),context);
const original={notes:[{timeMs:500,lane:1,durationMs:500,speedupCoef:0},{timeMs:1700,lane:1,durationMs:500,speedupCoef:0}],specialNotes:[
  {timeMs:500,durationMs:1000,effect:'delta',stageDelta:-4,label:'delta wind'},
  {timeMs:2500,durationMs:800,effect:'limit',maxSpeed:1.1,startMaxSpeed:1.8,label:'limit wind'},
  {timeMs:4000,durationMs:0,effect:'limit',maxSpeed:1}],timing:{bpm:180}};
context.projectImportChartData(original);
const output=JSON.parse(JSON.stringify(context.projectBuildBasePayload()));
assert.equal(output.version,4);
assert.equal(output.speedLimitLines,undefined);
assert.equal(output.stageDeltaLines,undefined);
assert.deepEqual(output.specialNotes,original.specialNotes.map(n=>{
 const next={...n};delete next.startMaxSpeed;
 if(n.effect==='delta'){next.speedDelta=n.stageDelta*.065;delete next.stageDelta;}return next;
}));
context.projectImportChartData({version:4,notes:[],specialNotes:[{timeMs:500,durationMs:10000,effect:'delta',speedDelta:-.2}]});
assert.equal(context.projectBuildBasePayload().specialNotes[0].speedDelta,-.2);
assert.equal(context.projectBuildBasePayload().specialNotes[0].stageDelta,undefined);
assert.equal(output.notes.length,2);
assert.equal(output.notes[0].timeMs,500);
assert.equal(output.notes[1].timeMs,1700);
assert.equal(output.notes[0].durationMs,500);
assert.equal(output.notes[0].lane,1);
context.projectImportChartData({notes:[],stageDeltaLines:[{timeMs:100,stageDelta:2}],speedLimitLines:[]});
assert.equal(context.projectBuildBasePayload().specialNotes[0].durationMs,0);
context.projectImportChartData({notes:[],stageDeltaLines:Array.from({length:10},(_,i)=>({timeMs:i*50,stageDelta:-.2}))});
assert.equal(context.projectBuildBasePayload().specialNotes.length,1);
assert.equal(context.projectBuildBasePayload().specialNotes[0].durationMs,450);
console.log('Special notes passed: full script syntax, canonical round-trip, labels, limit start, holds, overlaps and legacy import.');
