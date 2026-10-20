import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
const source=html.slice(html.indexOf("window.addEventListener('keydown',evt=>"),html.indexOf('\nfunction setTool('));
const calls=[];let handler;
const context={window:{addEventListener:(_,fn)=>handler=fn},document:{activeElement:{tagName:'DIV'}},state:{recordKeys:false,currentMode:'tap'},chartKeys:[],
setTool:v=>calls.push(['tool',v]),setCoef:(...v)=>calls.push(['coef',...v]),setMode:(...v)=>calls.push(['mode',...v]),undo:()=>calls.push(['undo']),redo:()=>calls.push(['redo']),projectSaveSelected:()=>calls.push(['save']),startPlayback:()=>calls.push(['play']),pausePlayback:()=>calls.push(['pause'])};
vm.runInNewContext(source,context);
function key(k,extra={}){calls.length=0;handler({key:k,preventDefault(){},...extra});return calls;}
assert.deepEqual(key('q'),[['tool','select']]);assert.deepEqual(key('w'),[['tool','place']]);assert.deepEqual(key('e'),[['tool','playhead']]);
assert.deepEqual(key('a'),[['coef',0,true]]);assert.deepEqual(key('s'),[['coef',1,true]]);assert.deepEqual(key('d'),[['mode','hold',true]]);
assert.deepEqual(key('1'),[['tool','select']]);assert.deepEqual(key('2'),[['tool','place'],['mode','tap',true]]);assert.deepEqual(key('3'),[['tool','place'],['mode','hold',true]]);
assert.deepEqual(key('s',{ctrlKey:true}),[['save']]);assert.deepEqual(key('z',{ctrlKey:true}),[['undo']]);assert.deepEqual(key('z',{ctrlKey:true,shiftKey:true}),[['redo']]);
assert.deepEqual(key('d',{repeat:true}),[]);context.document.activeElement.tagName='INPUT';assert.deepEqual(key('a'),[]);
console.log('Editor shortcuts passed: left-hand tools, coef, hold, osu aliases, save, redo, repeat and typing guards.');

// Toolbar labels execute outside the editor closure, so use the global DOM API.
const labels = new Map();
vm.runInNewContext(html.slice(html.lastIndexOf('for(const [id,label]'),html.indexOf('</script>',html.lastIndexOf('for(const [id,label]'))), {document:{getElementById(id){const el={};labels.set(id,el);return el;}}});
assert.equal(labels.get('coef0Btn').textContent,'Coef 0 [A]');
assert.equal(labels.get('coef1Btn').textContent,'Coef 1 [S]');
