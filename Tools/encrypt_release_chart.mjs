#!/usr/bin/env node
// Read the unlock phrase from stdin; never put it in a command argument or source file.
import { createCipheriv, createDecipheriv, createHmac, pbkdf2Sync, randomBytes } from 'node:crypto';
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline';

const [source, destination, argId, releaseAudioName] = process.argv.slice(2);
if (!source || !destination || !/^[0-9a-f]{32}$/.test(argId) ||
    !/^[a-z0-9][a-z0-9._-]*\.(wav|mp3|ogg|flac)$/.test(releaseAudioName || '')) {
  throw new Error('Usage: node encrypt_release_chart.mjs SOURCE OUTPUT OPAQUE_ARG_ID RELEASE_AUDIO_NAME');
}

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

const schemaVersion = 1, iterations = 600000;
const salt = randomBytes(16), iv = randomBytes(16);
const key = pbkdf2Sync(phrase, salt, iterations, 64, 'sha256');
const aad = Buffer.from(`OverTempo.otchart|${schemaVersion}|${argId}`, 'utf8');
try {
  const cipher = createCipheriv('aes-256-cbc', key.subarray(0, 32), iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = createHmac('sha256', key.subarray(32)).update(aad).update(iv).update(ciphertext).digest();
  const decipher = createDecipheriv('aes-256-cbc', key.subarray(0, 32), iv);
  const recovered = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  if (!recovered.equals(plaintext)) throw new Error('Encryption round trip failed.');
  recovered.fill(0);
  const envelope = {
    schemaVersion, argId, cipher: 'AES-256-CBC+HMAC-SHA256',
    kdf: 'PBKDF2-HMAC-SHA256', iterations,
    salt: salt.toString('base64'), iv: iv.toString('base64'),
    ciphertext: ciphertext.toString('base64'), tag: tag.toString('base64'),
  };
  writeFileSync(destination + '.tmp', JSON.stringify(envelope, null, 2) + '\n');
  renameSync(destination + '.tmp', destination);
  process.stdout.write(`Encrypted and verified ${argId}.\n`);
} finally {
  key.fill(0);
  plaintext.fill(0);
}
