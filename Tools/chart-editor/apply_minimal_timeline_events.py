#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
SERVER = ROOT / "server.py"

TIMELINE_CARD = '''<div class="card"><h3>Timeline Events</h3>
<div class="small">
Speed Limit Line: 해당 시점에서 현재 배속이 max보다 크면 제한합니다.<br>
Stage Delta Line: 해당 시점에서 stage에 delta를 더합니다.
</div>
<div class="grid2">
<label>Limit Max Speed <input id="speedLimitMaxInput" type="number" value="1.25" min="1" step="0.01"></label>
<label>Stage Delta <input id="stageDeltaInput" type="number" value="-5" step="0.1"></label>
</div>
<div class="row">
<button id="addSpeedLimitLineBtn">Add Limit @ Playhead</button>
<button id="addStageDeltaLineBtn">Add Delta @ Playhead</button>
</div>
<div class="note-list" id="timelineEventList"></div>
</div>'''

DRAW_TIMELINE_EVENTS = r'''function drawTimelineEvents(W,H,a){
 const start=state.viewStartMs-500;
 const end=state.viewStartMs+(H/state.pxPerSecond)*1000+500;
 const drawEventLine=(timeMs,text,color)=>{
  if(timeMs<start||timeMs>end)return;
  const y=msToY(timeMs);
  ctx.save();
  ctx.strokeStyle=color;
  ctx.lineWidth=2;
  ctx.setLineDash([7,5]);
  ctx.beginPath();
  ctx.moveTo(a.left,y);
  ctx.lineTo(a.right,y);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle=color;
  ctx.font='12px ui-monospace,monospace';
  ctx.fillText(text,a.left+8,y-6);
  ctx.restore();
 };
 for(const line of state.speedLimitLines||[]){
  drawEventLine(
   Number(line.timeMs)||0,
   `LIMIT <= ${Number(line.maxSpeed||1).toFixed(2)}x`,
   'rgba(255,107,122,.95)'
  );
 }
 for(const line of state.stageDeltaLines||[]){
  const d=Number(line.stageDelta)||0;
  drawEventLine(
   Number(line.timeMs)||0,
   `STAGE ${d>=0?'+':''}${d.toFixed(2)}`,
   'rgba(134,215,255,.95)'
  );
 }
}
'''

TIMELINE_FUNCTIONS = r'''function sortTimelineEvents(){
 state.speedLimitLines=(state.speedLimitLines||[]).sort((a,b)=>(Number(a.timeMs)||0)-(Number(b.timeMs)||0));
 state.stageDeltaLines=(state.stageDeltaLines||[]).sort((a,b)=>(Number(a.timeMs)||0)-(Number(b.timeMs)||0));
}
function updateTimelineEventList(){
 const list=$('timelineEventList');
 if(!list)return;
 sortTimelineEvents();
 list.innerHTML='';
 const rows=[];
 (state.speedLimitLines||[]).forEach((line,index)=>{
  rows.push({
   kind:'limit',
   index,
   timeMs:Number(line.timeMs)||0,
   text:`${Math.round(Number(line.timeMs)||0)}ms / LIMIT <= ${Number(line.maxSpeed||1).toFixed(2)}x`
  });
 });
 (state.stageDeltaLines||[]).forEach((line,index)=>{
  const d=Number(line.stageDelta)||0;
  rows.push({
   kind:'delta',
   index,
   timeMs:Number(line.timeMs)||0,
   text:`${Math.round(Number(line.timeMs)||0)}ms / STAGE ${d>=0?'+':''}${d.toFixed(2)}`
  });
 });
 rows.sort((a,b)=>a.timeMs-b.timeMs);
 for(const row of rows){
  const item=document.createElement('div');
  item.className='note-item';
  item.style.gridTemplateColumns='1fr auto';
  item.innerHTML=`<span>${row.text}</span><button data-kind="${row.kind}" data-index="${row.index}">Delete</button>`;
  item.onclick=e=>{
   if(e.target&&e.target.tagName==='BUTTON')return;
   state.playheadMs=row.timeMs;
   state.viewStartMs=Math.max(0,row.timeMs-1600);
   updatePanels();
  };
  item.querySelector('button').onclick=()=>{
   pushHistory();
   if(row.kind==='limit')state.speedLimitLines.splice(row.index,1);
   else state.stageDeltaLines.splice(row.index,1);
   updatePanels();
  };
  list.appendChild(item);
 }
}
function addSpeedLimitLineAtPlayhead(){
 const maxSpeed=Math.max(1,Number($('speedLimitMaxInput').value)||1);
 pushHistory();
 state.speedLimitLines.push({
  timeMs:Math.max(0,Math.round(snapTime(state.playheadMs))),
  maxSpeed
 });
 updatePanels();
}
function addStageDeltaLineAtPlayhead(){
 const stageDelta=Number($('stageDeltaInput').value)||0;
 pushHistory();
 state.stageDeltaLines.push({
  timeMs:Math.max(0,Math.round(snapTime(state.playheadMs))),
  stageDelta
 });
 updatePanels();
}
function exportSpeedLimitLines(){
 sortTimelineEvents();
 return (state.speedLimitLines||[]).map(line=>({
  timeMs:Math.max(0,Math.round(Number(line.timeMs)||0)),
  maxSpeed:Math.max(1,Number(line.maxSpeed)||1)
 }));
}
function exportStageDeltaLines(){
 sortTimelineEvents();
 return (state.stageDeltaLines||[]).map(line=>({
  timeMs:Math.max(0,Math.round(Number(line.timeMs)||0)),
  stageDelta:Number(line.stageDelta)||0
 }));
}
'''

IMPORT_LINES = r'''state.speedLimitLines=(data.speedLimitLines||[]).map(line=>({
 timeMs:Math.max(0,Math.round(Number(line.timeMs)||0)),
 maxSpeed:Math.max(1,Number(line.maxSpeed)||1)
}));
state.stageDeltaLines=(data.stageDeltaLines||[]).map(line=>({
 timeMs:Math.max(0,Math.round(Number(line.timeMs)||0)),
 stageDelta:Number(line.stageDelta)||0
}));
'''


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"marker for {label} not found exactly once; found {count}")
    return text.replace(old, new, 1)


def insert_before_once(text: str, marker: str, insert: str, label: str) -> str:
    count = text.count(marker)
    if count != 1:
        fail(f"marker for {label} not found exactly once; found {count}")
    return text.replace(marker, insert + marker, 1)


def replace_one_of(text: str, options: list[str], replacement_factory, label: str) -> str:
    matches = [old for old in options if text.count(old) == 1]
    if len(matches) != 1:
        counts = {old: text.count(old) for old in options}
        fail(f"marker for {label} not found exactly once among options; counts={counts}")
    old = matches[0]
    return text.replace(old, replacement_factory(old), 1)


def patch_index() -> bool:
    if not INDEX.exists():
        fail(f"index.html not found at {INDEX}")

    text = INDEX.read_text(encoding="utf-8")

    # Refuse to patch the previously broken generated editor. The current GitHub editor's hold rendering has this body shape.
    if "ctx.fillRect(x+w*.30,top,w*.40,h);" not in text or "roundRect(ctx,x,y2-7,w,14,6,true,true)" not in text:
        fail(
            "index.html does not look like the current GitHub chart editor. "
            "Restore it first, e.g. git checkout HEAD -- Tools/chart-editor/index.html, then rerun this script."
        )

    if "speedLimitLines" in text or "addSpeedLimitLineBtn" in text:
        print("index.html already appears to contain timeline event additions; no changes made.")
        return False

    original = text

    # State additions.
    text = replace_once(
        text,
        "project:{available:false,songs:[],songName:'',chartName:'',audioName:'',pendingNewSong:null},autoCoef:",
        "project:{available:false,songs:[],songName:'',chartName:'',audioName:'',pendingNewSong:null},speedLimitLines:[],stageDeltaLines:[],autoCoef:",
        "state timeline arrays",
    )

    # Undo/redo snapshot additions.
    text = replace_once(
        text,
        "coverDataUrl:state.coverDataUrl,autoCoef:",
        "coverDataUrl:state.coverDataUrl,speedLimitLines:(state.speedLimitLines||[]).map(x=>({...x})),stageDeltaLines:(state.stageDeltaLines||[]).map(x=>({...x})),autoCoef:",
        "snapshot timeline arrays",
    )
    text = replace_once(
        text,
        "state.coverDataUrl=d.coverDataUrl||'';if(d.autoCoef){",
        "state.coverDataUrl=d.coverDataUrl||'';state.speedLimitLines=(d.speedLimitLines||[]).map(x=>({...x}));state.stageDeltaLines=(d.stageDeltaLines||[]).map(x=>({...x}));if(d.autoCoef){",
        "restore timeline arrays",
    )

    # UI card. Insert between Chart card and Auto Coef card.
    text = replace_once(
        text,
        "<div class=\"card\"><h3>Auto Coef / Difficulty Curve</h3>",
        TIMELINE_CARD + "\n<div class=\"card\"><h3>Auto Coef / Difficulty Curve</h3>",
        "timeline event UI card",
    )

    # Draw event lines without touching drawNote.
    text = replace_once(
        text,
        "drawAutoCoefCurve(W,H,a);drawNotes(a);",
        "drawAutoCoefCurve(W,H,a);drawTimelineEvents(W,H,a);drawNotes(a);",
        "draw timeline events call",
    )
    text = insert_before_once(text, "function drawNotes(a){", DRAW_TIMELINE_EVENTS, "drawTimelineEvents function")

    # Management functions.
    text = insert_before_once(text, "function playHit(", TIMELINE_FUNCTIONS, "timeline event management functions")

    # Panel refresh.
    text = replace_once(
        text,
        "autoCoefUpdateStats();updateNoteList();updateUndoRedoButtons()}",
        "autoCoefUpdateStats();updateNoteList();updateTimelineEventList();updateUndoRedoButtons()}",
        "updatePanels timeline list refresh",
    )

    # Project import: insert after first state.notes map in projectImportChartData.
    text = replace_once(
        text,
        "durationMs:Math.max(0,Math.round(n.durationMs||n.duration||0))\n  }));\n  state.meta=",
        "durationMs:Math.max(0,Math.round(n.durationMs||n.duration||0))\n  }));\n  " + IMPORT_LINES.replace("\n", "\n  ") + "state.meta=",
        "projectImportChartData timeline import",
    )

    # Project save payload.
    text = replace_once(
        text,
        "preview:{startMs:state.meta.previewStartMs,endMs:state.meta.previewEndMs},\n    notes:",
        "preview:{startMs:state.meta.previewStartMs,endMs:state.meta.previewEndMs},\n    speedLimitLines:exportSpeedLimitLines(),\n    stageDeltaLines:exportStageDeltaLines(),\n    notes:",
        "projectBuildBasePayload timeline export",
    )

    # Local export payload.
    text = replace_once(
        text,
        "preview:{startMs:state.meta.previewStartMs,endMs:state.meta.previewEndMs},notes:",
        "preview:{startMs:state.meta.previewStartMs,endMs:state.meta.previewEndMs},speedLimitLines:exportSpeedLimitLines(),stageDeltaLines:exportStageDeltaLines(),notes:",
        "exportJson timeline export",
    )

    # Local JSON import. This exact inline parser appears in importJsonFile.
    text = replace_once(
        text,
        "durationMs:Math.max(0,Math.round(n.durationMs||n.duration||0))}));state.meta=",
        "durationMs:Math.max(0,Math.round(n.durationMs||n.duration||0))}));" + IMPORT_LINES.replace("\n", "") + "state.meta=",
        "importJsonFile timeline import",
    )

    # Button bindings. Preserve whether the original file has a newline before window.addEventListener.
    text = replace_one_of(
        text,
        [
            "$('projectSaveBtn').onclick=()=>projectSaveSelected();window.addEventListener('resize',resize);",
            "$('projectSaveBtn').onclick=()=>projectSaveSelected();\nwindow.addEventListener('resize',resize);",
        ],
        lambda old: old.replace("$('projectSaveBtn').onclick=()=>projectSaveSelected();", "$('projectSaveBtn').onclick=()=>projectSaveSelected();$('addSpeedLimitLineBtn').onclick=addSpeedLimitLineAtPlayhead;$('addStageDeltaLineBtn').onclick=addStageDeltaLineAtPlayhead;"),
        "timeline event button bindings",
    )

    backup = INDEX.with_suffix(INDEX.suffix + ".bak-before-timeline-events")
    shutil.copy2(INDEX, backup)
    INDEX.write_text(text, encoding="utf-8", newline="")

    print(f"Patched index.html. Backup written to {backup.name}.")
    print("Unchanged by design: drawNote, addNote, hold resize logic, autoCoefGenerateCurve, projectBuildPayload auto-coef section.")
    return text != original


def patch_server() -> bool:
    if not SERVER.exists():
        print("server.py not found; skipped server patch.")
        return False

    text = SERVER.read_text(encoding="utf-8")
    if '"speedLimitLines"' in text:
        print("server.py already contains blank timeline arrays; no changes made.")
        return False

    old = '''        "preview": {
            "startMs": 0,
            "endMs": 15000,
        },
        "notes": [],
'''
    new = '''        "preview": {
            "startMs": 0,
            "endMs": 15000,
        },
        "speedLimitLines": [],
        "stageDeltaLines": [],
        "notes": [],
'''
    if old not in text:
        print("server.py blank-chart marker not found; skipped server patch.")
        return False

    backup = SERVER.with_suffix(SERVER.suffix + ".bak-before-timeline-events")
    shutil.copy2(SERVER, backup)
    SERVER.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"Patched server.py. Backup written to {backup.name}.")
    return True


def main() -> None:
    patch_index()
    patch_server()
    print("Done.")


if __name__ == "__main__":
    main()
