#!/usr/bin/env node
/**
 * Pretendard OTF -> WOFF2, so the landing page needs no font CDN (2026-11-06, legal sweep A8: no Google Fonts or jsDelivr request from a visitor's browser).
 * Source = the app's own files (../string-ai-app/assets/fonts, SIL OFL, Reserved Font Name Pretendard). Only the packaging changes: every table goes in unchanged except the
 * one flag the WOFF2 spec asks an encoder to set (head.flags bit 11), no subsetting, no renaming. Node's own Brotli, nothing to install.
 * usage: node scripts/build-fonts.mjs [--app-dir ../string-ai-app]
 */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(HERE, '..');
const at = process.argv.indexOf('--app-dir');
const APP = at > 0 ? path.resolve(process.argv[at + 1]) : path.resolve(SITE, '..', 'string-ai-app');
const OUT = path.join(SITE, 'assets', 'fonts');
const FACES = ['Regular', 'Bold'];

// WOFF2 known table tags (W3C WOFF2 §4.1). Anything else is written out with index 63.
const KNOWN = ['cmap', 'head', 'hhea', 'hmtx', 'maxp', 'name', 'OS/2', 'post', 'cvt ', 'fpgm', 'glyf', 'loca', 'prep', 'CFF ', 'VORG', 'EBDT', 'EBLC', 'gasp', 'hdmx', 'kern', 'LTSH', 'PCLT', 'VDMX', 'vhea', 'vmtx', 'BASE', 'GDEF', 'GPOS', 'GSUB'];

function base128(n) {
  const out = [];
  for (let shift = 28, started = false; shift >= 0; shift -= 7) {
    const part = (n >>> shift) & 0x7f;
    if (part !== 0 || started || shift === 0) { out.push(part | (shift === 0 ? 0 : 0x80)); started = true; }
  }
  return Buffer.from(out);
}

function encode(otf) {
  if (otf.toString('latin1', 0, 4) !== 'OTTO') throw new Error('expected a CFF OpenType font');
  const numTables = otf.readUInt16BE(4);
  const tables = [];
  for (let i = 0; i < numTables; i += 1) {
    const rec = 12 + i * 16;
    const tag = otf.toString('latin1', rec, rec + 4);
    if (tag === 'DSIG') throw new Error('signed font: WOFF2 requires dropping DSIG, look at it first');
    tables.push({ tag, data: Buffer.from(otf.subarray(otf.readUInt32BE(rec + 8), otf.readUInt32BE(rec + 8) + otf.readUInt32BE(rec + 12))) });
  }
  const head = tables.find((t) => t.tag === 'head');
  head.data.writeUInt16BE(head.data.readUInt16BE(16) | 0x0800, 16); // spec: lossless-compressed font data
  const directory = Buffer.concat(tables.map(({ tag, data }) => {
    const known = KNOWN.indexOf(tag);
    return Buffer.concat([known >= 0 ? Buffer.from([known]) : Buffer.concat([Buffer.from([63]), Buffer.from(tag, 'latin1')]), base128(data.length)]);
  }));
  const raw = Buffer.concat(tables.map((t) => t.data));
  const compressed = zlib.brotliCompressSync(raw, { params: {
    [zlib.constants.BROTLI_PARAM_MODE]: zlib.constants.BROTLI_MODE_FONT,
    [zlib.constants.BROTLI_PARAM_QUALITY]: 11,
    [zlib.constants.BROTLI_PARAM_LGWIN]: 24,
    [zlib.constants.BROTLI_PARAM_SIZE_HINT]: raw.length,
  } });
  const body = 48 + directory.length + compressed.length;
  const length = (body + 3) & ~3; // a decoder rounds the end of the stream up to four bytes
  const header = Buffer.alloc(48);
  header.write('wOF2', 0, 'latin1');
  header.write('OTTO', 4, 'latin1');
  header.writeUInt32BE(length, 8);
  header.writeUInt16BE(numTables, 12);
  header.writeUInt32BE(otf.length, 16);
  header.writeUInt32BE(compressed.length, 20);
  header.writeUInt16BE(head.data.readUInt16BE(4), 24); // font version from head.fontRevision
  header.writeUInt16BE(head.data.readUInt16BE(6), 26);
  return Buffer.concat([header, directory, compressed, Buffer.alloc(length - body)]);
}

fs.mkdirSync(OUT, { recursive: true });
for (const face of FACES) {
  const otf = fs.readFileSync(path.join(APP, 'assets', 'fonts', `Pretendard-${face}.otf`));
  const woff2 = encode(otf);
  fs.writeFileSync(path.join(OUT, `Pretendard-${face}.woff2`), woff2);
  console.log(`Pretendard-${face}: ${otf.length} -> ${woff2.length} bytes`);
}
fs.copyFileSync(path.join(APP, 'assets', 'fonts', 'PRETENDARD-LICENSE-OFL.txt'), path.join(OUT, 'PRETENDARD-LICENSE-OFL.txt'));
