import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(new URL('./index.html',import.meta.url),'utf8');
new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
function source(start,end){return html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));}
const context={state:{effects:[],images:[],notes:[]},Math,JSON};
vm.createContext(context);
vm.runInContext(source('/* ===== Chart effects','/* --- End Time glass'),context);
const E=(type,group,timeMs,durationMs,value,ease='linear')=>({type,group,timeMs,durationMs,value,ease});
// Same expectations as Assets/Editor/ChartEffectsTests.cs
let m=context.chartEffectsModel([E('alpha','g',1000,0,.2),E('alpha','g',2000,1000,1),E('alpha','g',4000,0,0)].map(context.normalizeEffect));
const near=(a,b,eps=1e-4)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
near(m.alphaAt('g',.9),1);near(m.alphaAt('g',1),.2);near(m.alphaAt('g',2.5),.6);near(m.alphaAt('g',3.5),1);near(m.alphaAt('g',4),0);
m=context.chartEffectsModel([E('speed','g',1000,0,2),E('speed','g',3000,2000,0,'inOutQuad')].map(context.normalizeEffect));
near(m.distanceFactor('other',0,5),1);near(m.distanceFactor('g',.5,2),1);near(m.distanceFactor('g',1.5,2),2);near(m.distanceFactor('g',1.5,3),m.distanceFactor('g',1.5,9));near(m.distanceFactor('g',4,9),1,1e-4);near(m.distanceFactor('g',6,9),0);
m=context.chartEffectsModel([E('alpha','g',0,1000,0),E('alpha','g',500,0,1)].map(context.normalizeEffect));
near(m.alphaAt('g',.25),.75);near(m.alphaAt('g',.6),1);
m=context.chartEffectsModel([context.normalizeEffect({type:'glitch',timeMs:1000,durationMs:1000,intensity:.2,intensityEnd:1})]);
near(m.glitchAt(999),0);near(m.glitchAt(1500),.6);near(m.glitchAt(2001),0);
// Round trip through import/export keeps groups, triggers and images.
context.importEffects({effects:[{type:'shatter',timeMs:2000,durationMs:500,reveal:'pic'},{type:'restore',timeMs:4000,durationMs:800,style:'wipe',direction:'left'},{type:'bogus'}],
 images:[{id:'pic',dataUrl:'data:image/png;base64,AAAA',timeMs:3000,width:.5},{id:'bad',dataUrl:'http://x'}]});
const fx=context.exportEffects(),imgs=context.exportImages();
assert.equal(fx.length,2);assert.equal(fx[0].reveal,'pic');assert.equal(fx[0].freeze,true);assert.equal(fx[0].breakMs,1400);assert.equal(fx[1].direction,'left');
assert.equal(imgs.length,1);assert.equal(imgs[0].width,.5);assert.equal(imgs[0]._id,undefined);
console.log('effects editor tests passed');
// Auto mode simulation (GameManager autoplay with acceleration): every head/hold end is PERFECT.
{
 const ctx2={state:{notes:[],stageDeltaLines:[],speedLimitLines:[],autoCoef:{curve:[]}},Math,JSON,Number,Infinity,
  gamePreview:{geometry:{speedMultiplier:.065,perfectThreshold:.1}},autoCoefPointAt:()=>({multiplier:1}),$:()=>({checked:true})};
 vm.createContext(ctx2);vm.runInContext(source('/* --- Auto mode','function drawHudTexts('),ctx2);
 ctx2.state.notes=Array.from({length:10},(_,i)=>({timeMs:1000+i*100,lane:0,durationMs:0,speedupCoef:1}));
 ctx2.state.notes.push({timeMs:3000,lane:1,durationMs:1000,speedupCoef:1},{timeMs:3500,lane:2,durationMs:0,speedupCoef:0});
 const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
 near(ctx2.autoSpeedAt(999),1);near(ctx2.autoSpeedAt(1000),1+.065*.1);near(ctx2.autoSpeedAt(2000),1+.065*.1*10);
 near(ctx2.autoSpeedAt(3600),1+.065*.1*11);near(ctx2.autoSpeedAt(4000),1+.065*.1*12); // hold end counts, coef 0 does not
 // wall clock: chart time runs faster as speed rises
 assert.ok(ctx2.autoWallMsAt(2000)<2000&&ctx2.autoWallMsAt(1000)===1000);
 ctx2.state.speedLimitLines=[{timeMs:5000,durationMs:0,maxSpeed:1}];ctx2.state.stageDeltaLines=[{timeMs:6000,durationMs:1000,speedDelta:.2}];
 near(ctx2.autoSpeedAt(5000),1);near(ctx2.autoSpeedAt(6500),1.1);near(ctx2.autoSpeedAt(7000),1.2);
 console.log('auto mode simulation tests passed');
}
// Group ranges: every note inside a group block's time range (and lanes) belongs to that group.
{
 const ctx3={state:{notes:[{timeMs:100,lane:0},{timeMs:500,lane:1},{timeMs:900,lane:2},{timeMs:500,lane:3,group:'old'}],
  fxGroupBlocks:[{id:'a',startMs:400,endMs:1000,lanes:[0,1,2]},{id:'b',startMs:850,endMs:950,lanes:[2]}],groupBlocksAuthoritative:true}};
 vm.createContext(ctx3);vm.runInContext(source('let nextGroupUid=1;','function groupColorOf('),ctx3);
 ctx3.syncGroupMembership();
 assert.deepEqual(ctx3.state.notes.map(n=>n.group??''),['','a','b','']); // later block wins; lane 4 excluded; stale group cleared
 console.log('group range membership tests passed');
}
// Start + end values for group alpha/speed (ChartEffects.cs fromValue)
{
 const fade=context.normalizeEffect({type:'alpha',group:'g',timeMs:1000,durationMs:1000,value:.2,fromValue:.8});
 assert.equal(fade.fromValue,.8);
 const mdl=context.chartEffectsModel([context.normalizeEffect({type:'alpha',group:'g',timeMs:0,durationMs:0,value:0}),fade]);
 const near=(a,b,eps=1e-4)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
 near(mdl.alphaAt('g',.9),0);near(mdl.alphaAt('g',1),.8);near(mdl.alphaAt('g',1.5),.5);near(mdl.alphaAt('g',2.5),.2);
 assert.equal(context.normalizeEffect({type:'speed',group:'g',timeMs:0,value:2}).fromValue,undefined);
 near(context.chartEffectsModel([context.normalizeEffect({type:'speed',group:'g',timeMs:0,durationMs:1000,fromValue:1,value:3})]).distanceFactor('g',.5,1),2,1e-3);
 console.log('start/end value tests passed');
}
// Custom curves (Unity AnimationCurve style) — same numbers as ChartEffectsTests.CustomCurveIsHermiteLikeUnityAnimationCurve
{
 const ctx4={Math,Number,Array,JSON};vm.createContext(ctx4);vm.runInContext(source('function fxCurveEval(','function fxEase('),ctx4);
 const near=(a,b,eps=1e-4)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
 const smooth=[{t:0,v:0,inTan:0,outTan:0},{t:1,v:1,inTan:0,outTan:0}];
 near(ctx4.fxCurveEval(smooth,.25),.15625);near(ctx4.fxCurveEval(smooth,.5),.5);
 const stepped=[{t:0,v:0,inTan:0,outTan:0,stepped:true},{t:.5,v:1,inTan:0,outTan:0},{t:1,v:1,inTan:0,outTan:0}];
 near(ctx4.fxCurveEval(stepped,.49),0);near(ctx4.fxCurveEval(stepped,.5),1);
 const fade=context.normalizeEffect({type:'alpha',group:'g',timeMs:0,durationMs:1000,fromValue:1,value:0,curve:smooth});
 assert.equal(fade.curve.length,2);near(context.chartEffectsModel([fade]).alphaAt('g',.25),1-.15625);
 console.log('curve tests passed');
}
// Group position offset in 1/12 beats (ChartEffectsTests.OffsetShiftsDrawTimeInTwelfthBeats)
{
 context.tempoSegmentAt=ms=>({bpm:ms>=10000?240:120});
 const shift=context.normalizeEffect({type:'offset',group:'g',timeMs:1000,durationMs:1000,fromValue:0,value:-1});
 assert.equal(shift.value,-1);assert.equal(shift.fromValue,0);
 const mdl=context.chartEffectsModel([shift]);const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-5,`${a} != ${b}`);
 near(mdl.visualHitTime('g',.5,5),5);near(mdl.visualHitTime('g',1.5,5),5-.5/12*.5);near(mdl.visualHitTime('g',3,5),5-.5/12);near(mdl.visualHitTime('g',3,12),12-.25/12);near(mdl.visualHitTime('h',3,5),5);
 assert.ok(mdl.hasGroupEffects('g'));
 assert.equal(context.normalizeEffect({type:'offset',group:'g',timeMs:0,value:-500,fromValue:1000}).value,-500); // no limit
 assert.equal(context.normalizeEffect({type:'offset',group:'g',timeMs:0,value:-500,fromValue:1000}).fromValue,1000);
 near(context.chartEffectsModel([context.normalizeEffect({type:'offset',group:'g',timeMs:0,value:-300})]).visualHitTime('g',1,5),5-300*.5/12);
 console.log('offset tests passed');
}
