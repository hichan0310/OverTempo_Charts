import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
const source=html.slice(html.indexOf('let projectPendingAutosave='),html.indexOf('async function projectSaveSelected'));
const flush=()=>new Promise(resolve=>setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject};}
function fixture(){
  const elements={projectSongSelect:{value:'New Song'},projectChartSelect:{value:'New.json'},projectAudioSelect:{value:'new.ogg'},coverPreview:{removeAttribute(){}}};
  const calls=[],alerts=[],overlay={style:{}},app={};
  const oldNotes=[{timeMs:123,lane:2,speedupCoef:0}];
  const context={console:{error(){}},encodeURIComponent,Promise,
    document:{querySelector:()=>app,getElementById:()=>overlay},
    state:{project:{songName:'Old Song',chartName:'Old.json',audioName:'old.ogg',loadedSelectionKey:'Old Song\0Old.json',loadToken:0,isLoading:false},notes:oldNotes,meta:{},audioFileName:'old.ogg'},
    $:id=>elements[id],alert:message=>alerts.push(message),history:{undo:[],redo:[]},
    projectSelectedSongName:()=>elements.projectSongSelect.value,projectSelectedChartName:()=>elements.projectChartSelect.value,projectSelectedAudioName:()=>elements.projectAudioSelect.value,
    projectSelectionKey:(song=elements.projectSongSelect.value,chart=elements.projectChartSelect.value)=>song&&chart?`${song}\0${chart}`:'',
    projectLoadIsCurrent:(token,key)=>token===context.state.project.loadToken&&key===context.projectSelectionKey(),
    projectSetStatus:message=>calls.push(['status',message]),projectUpdateActionAvailability(){},
    projectPopulateCharts:chart=>{elements.projectChartSelect.value=chart},projectPopulateAudio:audio=>{elements.projectAudioSelect.value=audio},
    projectBuildPayload:()=>({meta:{audioFileName:elements.projectAudioSelect.value},notes:JSON.parse(JSON.stringify(context.state.notes))}),
    projectSongByName:()=>({audio:[],covers:[]}),projectImportChartData:data=>{context.state.notes=data.notes;return 0},
    updateUndoRedoButtons(){},stopBgm(){},syncStateToUi(){},updatePanels(){},
    projectFetchJson:async(url,options)=>{calls.push([options?.method||'GET',url,options?.body]);return options?{}:{notes:[{timeMs:999,lane:0}],meta:{}}}
  };
  vm.createContext(context);vm.runInContext(source,context);
  return {context,elements,calls,alerts,app,oldNotes};
}
{
  const f=fixture(),saved=deferred();
  const fetch=f.context.projectFetchJson;
  f.context.projectFetchJson=(url,options)=>options?(f.calls.push(['POST',url,options.body]),saved.promise):fetch(url,options);
  const loading=f.context.projectLoadSelected();
  assert.equal(f.app.inert,true,'editing must pause during transition');
  assert.equal(f.calls.filter(c=>c[0]==='GET').length,0,'new chart loaded before save completed');
  const post=f.calls.find(c=>c[0]==='POST');
  assert.equal(post[1],'/api/chart?song=Old%20Song&chart=Old.json');
  assert.deepEqual(JSON.parse(post[2]),{meta:{audioFileName:'old.ogg'},notes:f.oldNotes},'destination path/audio contaminated the old chart');
  saved.resolve({});assert.equal(await loading,true);
  assert.equal(f.context.state.project.songName,'New Song');assert.equal(f.app.inert,false);
}
{
  const f=fixture();
  f.context.projectFetchJson=async(url,options)=>{f.calls.push([options?.method||'GET',url]);throw Error('disk full')};
  assert.equal(await f.context.projectLoadSelected(),false);
  assert.equal(f.calls.filter(c=>c[0]==='GET').length,0,'save failure must block loading');
  assert.equal(f.context.state.notes,f.oldNotes,'save failure discarded notes');
  assert.equal(f.elements.projectSongSelect.value,'Old Song');assert.equal(f.elements.projectChartSelect.value,'Old.json');
  assert.equal(f.context.state.project.loadedSelectionKey,'Old Song\0Old.json');
  assert.equal(f.app.inert,false);assert.match(f.alerts[0],/자동저장/);
}
{
  const f=fixture(),saved=deferred();const fetch=f.context.projectFetchJson;
  f.context.projectFetchJson=(url,options)=>options?(f.calls.push(['POST',url]),saved.promise):fetch(url,options);
  const first=f.context.projectLoadSelected();
  f.elements.projectSongSelect.value='Third Song';f.elements.projectChartSelect.value='Third.json';
  const last=f.context.projectLoadSelected();
  assert.equal(f.calls.filter(c=>c[0]==='POST').length,1,'rapid switches duplicated the autosave');
  saved.resolve({});assert.equal(await first,false);assert.equal(await last,true);
  assert.equal(f.context.state.project.songName,'Third Song');
  assert.equal(f.calls.filter(c=>c[0]==='GET').length,1,'stale destination was fetched');
}
{
  const f=fixture(),firstRead=deferred();const fetch=f.context.projectFetchJson;
  f.context.projectFetchJson=(url,options)=>!options&&url.endsWith('chart=New.json')?(f.calls.push(['GET',url]),firstRead.promise):fetch(url,options);
  const first=f.context.projectLoadSelected();await flush();
  f.elements.projectChartSelect.value='Alternate.json';
  const last=f.context.projectLoadSelected();assert.equal(await last,true);
  firstRead.resolve({notes:[{timeMs:1}],meta:{}});assert.equal(await first,false);
  assert.equal(f.context.state.project.chartName,'Alternate.json');
  assert.equal(f.context.state.notes[0].timeMs,999,'late load replaced latest chart');
  assert.equal(f.calls.filter(c=>c[0]==='POST').length,1,'partially loaded state was saved');
}
console.log('Autosave passed: old path/audio, save-before-load, failure preservation, rapid switches, stale loads, and input lock.');
