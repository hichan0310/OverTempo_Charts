#!/usr/bin/env node
// Creates the RSA key that signs ARG reveal packages (.otpack).
// The private key stays outside every repository; only the printed public key
// (modulus/exponent) is embedded in the game client (ArgRevealTrust.cs).
import { generateKeyPairSync, createPublicKey } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync, chmodSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

const path = process.env.OVERTEMPO_REVEAL_SIGNING_KEY ||
  join(homedir(), '.config', 'overtempo', 'arg-reveal-signing.pem');

if (!existsSync(path)) {
  const { privateKey } = generateKeyPairSync('rsa', { modulusLength: 3072, publicExponent: 0x10001 });
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  writeFileSync(path, privateKey.export({ type: 'pkcs8', format: 'pem' }), { mode: 0o600 });
  chmodSync(path, 0o600);
  process.stdout.write(`Created ${path} (back it up; it cannot be recovered).\n`);
} else {
  process.stdout.write(`Using existing ${path}\n`);
}

const jwk = createPublicKey(readFileSync(path)).export({ format: 'jwk' });
const b64 = (value) => Buffer.from(value, 'base64url').toString('base64');
process.stdout.write(`Modulus:  ${b64(jwk.n)}\nExponent: ${b64(jwk.e)}\n`);
