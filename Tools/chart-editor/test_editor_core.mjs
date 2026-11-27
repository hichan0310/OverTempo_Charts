import assert from "node:assert/strict";
import {
  createDecipheriv,
  createHmac,
  pbkdf2Sync,
  timingSafeEqual,
} from "node:crypto";
import { readFile } from "node:fs/promises";


const html = await readFile(new URL("./index.html", import.meta.url), "utf8");

function sourceBetween(start, end) {
  const startIndex = html.indexOf(start);
  const endIndex = html.indexOf(end, startIndex);
  assert.notEqual(startIndex, -1, `missing source marker: ${start}`);
  assert.notEqual(endIndex, -1, `missing source marker: ${end}`);
  return html.slice(startIndex, endIndex);
}

globalThis.window = globalThis;
globalThis.btoa = value => Buffer.from(value, "binary").toString("base64");

const cryptoSource = sourceBetween(
  "function normalizeSecretCode",
  "async function buildEncryptedRelease",
);
globalThis.eval(`${cryptoSource}
globalThis.editorCrypto = { normalizeSecretCode, encryptChartPayload };`);

assert.equal(
  editorCrypto.normalizeSecretCode("  teST   CiphEr\npHrase  "),
  "teST CiphEr pHrase",
);

const payload = {
  version: 2,
  timing: {
    bpm: 180,
    bpmChanges: [{ timeMs: 12000, bpm: 210 }],
  },
  notes: [{ timeMs: 1000, lane: 0 }],
};
const rawCode = "  teST   CiphEr pHrase ";
const argId = "arg_breaking_dawn";
const envelope = await editorCrypto.encryptChartPayload(payload, rawCode, argId);

const salt = Buffer.from(envelope.salt, "base64");
const iv = Buffer.from(envelope.iv, "base64");
const ciphertext = Buffer.from(envelope.ciphertext, "base64");
const tag = Buffer.from(envelope.tag, "base64");
const derived = pbkdf2Sync(
  "teST CiphEr pHrase",
  salt,
  envelope.iterations,
  64,
  "sha256",
);
const authenticated = Buffer.concat([
  Buffer.from(`OverTempo.otchart|1|${argId}`, "utf8"),
  iv,
  ciphertext,
]);
const expectedTag = createHmac("sha256", derived.subarray(32)).update(authenticated).digest();
assert.ok(timingSafeEqual(tag, expectedTag), "HMAC must match the Unity envelope contract");

const decipher = createDecipheriv("aes-256-cbc", derived.subarray(0, 32), iv);
const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
assert.deepEqual(JSON.parse(decrypted), payload);

globalThis.state = {
  bpm: 120,
  snapDiv: 4,
  playheadMs: 0,
  bpmChanges: [
    { timeMs: 2000, bpm: 60 },
    { timeMs: 1000, bpm: 240 },
  ],
};
const timingSource = sourceBetween(
  "function normalizedBpmChanges",
  "function msToY",
);
globalThis.eval(`${timingSource}
globalThis.editorTiming = { normalizedBpmChanges, tempoSegmentAt, beatMs, snapMs, snapTime };`);

assert.deepEqual(editorTiming.normalizedBpmChanges(), [
  { timeMs: 1000, bpm: 240 },
  { timeMs: 2000, bpm: 60 },
]);
assert.equal(editorTiming.beatMs(0), 500);
assert.equal(editorTiming.beatMs(1500), 250);
assert.equal(editorTiming.beatMs(2500), 1000);
assert.equal(editorTiming.snapMs(1500), 62.5);
assert.equal(editorTiming.snapTime(1124), 1125);
assert.equal(editorTiming.snapTime(980), 1000);

const elements = {
  projectSongSelect: { value: "Luminaria" },
  projectChartSelect: { value: "Luminaria_osu_base.4k-speedcoef.json" },
  projectAudioSelect: { value: "3-12 Luminaria.mp3", disabled: false },
  projectSaveBtn: { disabled: false },
  exportBtn: { disabled: false },
  autoExportBtn: { disabled: false },
  projectLoadBtn: { disabled: false },
  buildEncryptedChartBtn: { disabled: false },
};
globalThis.$ = id => elements[id] || null;
globalThis.state.project = {
  isLoading: true,
  loadToken: 4,
  loadedSelectionKey: "",
};
globalThis.state.encryption = { enabled: true };
const projectSelectionSource = sourceBetween(
  "function projectSelectedSongName",
  "async function projectFetchJson",
);
globalThis.eval(`${projectSelectionSource}
globalThis.editorProjectSelection = {
  projectSelectionKey,
  projectHasLoadedSelection,
  projectUpdateActionAvailability,
  projectLoadIsCurrent,
};`);

editorProjectSelection.projectUpdateActionAvailability();
assert.equal(elements.projectSaveBtn.disabled, true, "save must stay disabled while loading");
assert.equal(elements.autoExportBtn.disabled, true, "generated save must stay disabled while loading");
assert.equal(elements.buildEncryptedChartBtn.disabled, true, "encrypted save must stay disabled while loading");
const loadedKey = editorProjectSelection.projectSelectionKey();
state.project.isLoading = false;
state.project.loadedSelectionKey = loadedKey;
editorProjectSelection.projectUpdateActionAvailability();
assert.equal(elements.projectSaveBtn.disabled, false, "save may enable after the selected chart loaded");
elements.projectChartSelect.value = "Luminaria_Normal.4k-speedcoef.json";
assert.equal(editorProjectSelection.projectHasLoadedSelection(), false, "changing selection invalidates the loaded chart");
assert.equal(editorProjectSelection.projectLoadIsCurrent(4, loadedKey), false, "a stale load cannot apply to a new selection");

assert.match(html, /projectSongSelect'\)\.onchange=.*projectLoadSelected/);
assert.match(html, /projectChartSelect'\)\.onchange=.*projectLoadSelected/);

const initialSelectionSource = sourceBetween(
  "async function projectLoadInitialSelection",
  "function baseCoefFromNote",
);
globalThis.eval(`${initialSelectionSource}
globalThis.editorInitialSelection = projectLoadInitialSelection;`);
const initialCalls = [];
globalThis.location = {
  search: "?song=Chronomia&chart=Chronomia_AI_Advanced_Study.4k-speedcoef.json&timeMs=25000",
};
globalThis.projectRefreshSongs = async (...args) => initialCalls.push(args);
let finishInitialLoad;
let signalInitialLoad;
const initialLoadStarted = new Promise(resolve => { signalInitialLoad = resolve; });
globalThis.projectLoadSelected = () => {
  signalInitialLoad();
  return new Promise(resolve => { finishInitialLoad = resolve; });
};
globalThis.updatePanels = () => initialCalls.push("panels");
state.playheadMs = 0;
state.viewStartMs = 0;
const openingInitialSelection = editorInitialSelection();
await initialLoadStarted;
assert.deepEqual(initialCalls, [
  [false, "Chronomia", "Chronomia_AI_Advanced_Study.4k-speedcoef.json"],
]);
assert.equal(state.playheadMs, 0, "seek must wait for the selected chart and audio");
finishInitialLoad(true);
assert.equal(await openingInitialSelection, true);
assert.equal(state.playheadMs, 25000);
assert.equal(state.viewStartMs, 24500);
assert.equal(initialCalls.at(-1), "panels");
for (const search of ["", "?timeMs=-1", "?timeMs=invalid"]) {
  location.search = search;
  state.playheadMs = 123;
  state.viewStartMs = 50;
  globalThis.projectLoadSelected = async () => true;
  await editorInitialSelection();
  assert.equal(state.playheadMs, 123, "absent or invalid seek must preserve position");
  assert.equal(state.viewStartMs, 50);
}
location.search = "?timeMs=25000";
globalThis.projectLoadSelected = async () => false;
await editorInitialSelection();
assert.equal(state.playheadMs, 123, "failed chart load must not apply a seek");

// Given the actual audition functions and a deterministic Web Audio clock.
const auditionNodes = [];
const parameter = () => ({
  setValueAtTime() {},
  exponentialRampToValueAtTime() {},
});
globalThis.audioCtx = {
  currentTime: 10.05,
  destination: {},
  createOscillator() {
    const node = {
      frequency: parameter(),
      starts: [],
      stops: [],
      connect() {},
      start(when) { this.starts.push(when); },
      stop(when = audioCtx.currentTime) { this.stops.push(when); },
    };
    auditionNodes.push(node);
    return node;
  },
  createGain: () => ({ gain: parameter(), connect() {} }),
  createBiquadFilter: () => ({ frequency: parameter(), connect() {} }),
};
elements.hitVolume = { value: "0.65" };
globalThis.ensureAudioCtx = () => {};
globalThis.scheduledAuditions = [];
globalThis.bgmActive = true;
globalThis.bgmStartedChartMs = 25000;
globalThis.bgmStartedCtxTime = 10;
globalThis.bgmSource = null;
globalThis.bgmGain = null;
globalThis.audioStartedForThisPlayback = true;
state.playheadMs = 25045;
state.playbackRate = 1;
state.loop = false;
state.notes = [
  { timeMs: 25110, lane: 0, speedupCoef: 1 },
  { timeMs: 25242, lane: 2, speedupCoef: 0 },
];
globalThis.eval(
  sourceBetween("function playHit", "async function loadAudioFile") +
  sourceBetween("function stopBgm", "function startBgmAtChartTime") +
  sourceBetween("function auditionCrossedNotes", "function mousePos") +
  "globalThis.editorAudition = { auditionCrossedNotes, stopBgm };",
);
// When the next note is ahead of the current animation frame.
editorAudition.auditionCrossedNotes(16);
// Then it is already scheduled at its BGM context time, not frame arrival.
assert.equal(auditionNodes.length, 1, "future hits must be scheduled before their render frame");
assert.ok(Math.abs(auditionNodes[0].starts[0] - 10.11) < 1e-9);

// Given that the future hit has already been scheduled.
// When another frame visits the same look-ahead window.
editorAudition.auditionCrossedNotes(16);
// Then it is not scheduled a second time.
assert.equal(auditionNodes.length, 1);

// Given a queued future hit.
// When playback stops or resynchronizes.
editorAudition.stopBgm();
// Then the future oscillator is cancelled and its note may be scheduled again.
assert.equal(auditionNodes[0].stops.at(-1), audioCtx.currentTime);
assert.equal(state.notes[0]._lastPlayedAt, undefined);

// Given a replacement BGM source at 2x and a slightly lagging render frame.
bgmActive = true;
bgmStartedChartMs = 25050;
bgmStartedCtxTime = 10.05;
state.playheadMs = 25040;
state.playbackRate = 2;
// When scheduling from the new audio clock.
editorAudition.auditionCrossedNotes(16);
// Then both hits use the new rate/anchor, independent of render-frame jitter.
assert.equal(auditionNodes.length, 3);
assert.ok(Math.abs(auditionNodes[1].starts[0] - 10.08) < 1e-9);
assert.ok(Math.abs(auditionNodes[2].starts[0] - 10.146) < 1e-9);

// Given a loop ending exactly at the next event.
editorAudition.stopBgm();
bgmActive = true;
state.loop = true;
state.loopStartMs = 25000;
state.loopEndMs = 25110;
// When looking ahead across that boundary.
editorAudition.auditionCrossedNotes(16);
// Then no hit from outside the loop is queued.
assert.equal(auditionNodes.length, 3);

// Given a chart without active BGM and a muted hit channel.
editorAudition.stopBgm();
state.loop = false;
state.playbackRate = 1;
state.playheadMs = 25050;
elements.hitVolume.value = "0";
// When muted future hits are scheduled and playback stops.
editorAudition.auditionCrossedNotes(16);
editorAudition.stopBgm();
// Then cancellation needs no oscillator and does not leave the note consumed.
assert.equal(auditionNodes.length, 3);
assert.equal(state.notes[0]._lastPlayedAt, undefined);

console.log("editor crypto, timing, project loading, direct links, and audio-clock audition tests passed");
