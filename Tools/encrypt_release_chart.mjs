#!/usr/bin/env node
// Read the unlock phrase from stdin; never put it in a command argument or source file.
// Optional REVEAL_DIR (reveal.js + assets/) becomes OUTPUT_DIR/<argId>.otpack: signed with
// the developer key (Tools/arg_reveal_keygen.mjs) and encrypted under the same derived key.
import { createCipheriv, createDecipheriv, createHash, createHmac, createPrivateKey, createPublicKey,
  pbkdf2Sync, randomBytes, sign, verify } from 'node:crypto';
import { existsSync, readdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, extname, join } from 'node:path';
import { createInterface } from 'node:readline';

const [source, destination, argId, releaseAudioName, revealDir] = process.argv.slice(2);
if (!source || !destination || !/^[0-9a-f]{32}$/.test(argId) ||
    !/^[a-z0-9][a-z0-9._-]*\.(wav|mp3|ogg|flac)$/.test(releaseAudioName || '')) {
  throw new Error('Usage: node encrypt_release_chart.mjs SOURCE OUTPUT OPAQUE_ARG_ID RELEASE_AUDIO_NAME [REVEAL_DIR]');
}

// Limits mirror ArgRevealPackage.cs; the client rejects anything outside them.
const ASSET_NAME = /^[a-z0-9][a-z0-9._-]{0,63}$/;
const ASSET_EXTENSIONS = new Set(['.png', '.jpg', '.jpeg', '.wav', '.ogg', '.mp3']);
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
function buildRevealPackage(dir) {
  const script = readFileSync(join(dir, 'reveal.js'), 'utf8');
  if (Buffer.byteLength(script) > 256 * 1024) throw new Error('reveal.js exceeds 256 KiB.');
  const assets = [];
  const assetDir = join(dir, 'assets');
  let total = 0;
  if (existsSync(assetDir)) {
    for (const name of readdirSync(assetDir).filter((n) => !n.startsWith('.')).sort()) {
      if (!ASSET_NAME.test(name) || !ASSET_EXTENSIONS.has(extname(name))) throw new Error(`Unsupported asset name: ${name}`);
      const data = readFileSync(join(assetDir, name));
      total += data.length;
      if (data.length === 0 || data.length > 16 * 1024 * 1024 || total > 96 * 1024 * 1024 || assets.length >= 64) {
        throw new Error(`Asset limits exceeded at ${name}`);
      }
      assets.push({ name, data });
    }
  }
  let message = `OverTempo.otpack.v1\n${argId}\n${sha256(Buffer.from(script, 'utf8'))}\n`;
  for (const asset of [...assets].sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))) {
    message += `${asset.name}\n${sha256(asset.data)}\n`;
  }
  const keyPath = process.env.OVERTEMPO_REVEAL_SIGNING_KEY || join(homedir(), '.config', 'overtempo', 'arg-reveal-signing.pem');
  const privateKey = createPrivateKey(readFileSync(keyPath));
  const signature = sign('sha256', Buffer.from(message, 'utf8'), privateKey);
  if (!verify('sha256', Buffer.from(message, 'utf8'), createPublicKey(privateKey), signature)) throw new Error('Signature self-check failed.');
  const json = JSON.stringify({
    schemaVersion: 1, argId, script,
    assets: assets.map(({ name, data }) => ({ name, data: data.toString('base64') })),
    signature: signature.toString('base64'),
  });
  return Buffer.from(json, 'utf8');
}
function sealEnvelope(plaintext, key, salt, iterations, purpose) {
  const iv = randomBytes(16);
  const cipher = createCipheriv('aes-256-cbc', key.subarray(0, 32), iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const aad = Buffer.from(`${purpose}|1|${argId}`, 'utf8');
  const tag = createHmac('sha256', key.subarray(32)).update(aad).update(iv).update(ciphertext).digest();
  const decipher = createDecipheriv('aes-256-cbc', key.subarray(0, 32), iv);
  const recovered = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  if (!recovered.equals(plaintext)) throw new Error('Encryption round trip failed.');
  recovered.fill(0);
  return {
    schemaVersion: 1, argId, cipher: 'AES-256-CBC+HMAC-SHA256',
    kdf: 'PBKDF2-HMAC-SHA256', iterations,
    salt: salt.toString('base64'), iv: iv.toString('base64'),
    ciphertext: ciphertext.toString('base64'), tag: tag.toString('base64'),
  };
}
function writeAtomic(path, value) {
  writeFileSync(path + '.tmp', JSON.stringify(value, null, 2) + '\n');
  renameSync(path + '.tmp', path);
}
const revealPlaintext = revealDir ? buildRevealPackage(revealDir) : null;

const input = JSON.parse(readFileSync(source, 'utf8'));
if (!Array.isArray(input.notes) || input.notes.length === 0 || !input.meta) {
  throw new Error('Source chart must contain playable notes and metadata.');
}
delete input.editorSettings;
delete input.meta.coverDataUrl;
input.meta.audioFileName = releaseAudioName;
const plaintext = Buffer.from(JSON.stringify(input, null, 2), 'utf8');

const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
let phrase;
for await (const line of lines) { phrase = line.replace(/\s+/g, ' ').trim(); break; }
lines.close();
if (!phrase) throw new Error('Unlock phrase was empty.');

const iterations = 600000;
const salt = randomBytes(16);
const key = pbkdf2Sync(phrase, salt, iterations, 64, 'sha256');
const packagePath = join(dirname(destination), `${argId}.otpack`);
try {
  writeAtomic(destination, sealEnvelope(plaintext, key, salt, iterations, 'OverTempo.otchart'));
  if (revealPlaintext) {
    writeAtomic(packagePath, sealEnvelope(revealPlaintext, key, salt, iterations, 'OverTempo.otpack'));
    process.stdout.write(`Encrypted and verified ${argId} with signed reveal package.\n`);
  } else {
    // A package from an older salt could never decrypt; do not ship it.
    if (existsSync(packagePath)) unlinkSync(packagePath);
    process.stdout.write(`Encrypted and verified ${argId}.\n`);
  }
} finally {
  key.fill(0);
  plaintext.fill(0);
  if (revealPlaintext) revealPlaintext.fill(0);
}
