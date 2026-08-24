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

console.log("editor crypto, variable-BPM timing, and project load gating tests passed");
