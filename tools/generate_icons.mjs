// Optional development helper. Generated PNGs/SVG are shipped; users need no Node dependency.
import { createRequire } from 'node:module';
import { writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const option = process.argv.indexOf('--sharp-module');
const sharp = require(option >= 0 ? process.argv[option + 1] : 'sharp');
const root = fileURLToPath(new URL('../', import.meta.url));
const assets = path.join(root, 'plugins', 'experiment-learning', 'assets');
await mkdir(assets, { recursive: true });
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" role="img" aria-label="An open book with a clock">
  <title>Experiment Learning</title>
  <rect x="16" y="16" width="480" height="480" rx="104" fill="#0f172a"/>
  <path d="M98 138Q176 111 256 149V374Q175 338 98 363Z" fill="#f8fafc"/>
  <path d="M256 149Q336 111 414 138V363Q336 338 256 374Z" fill="#e2e8f0"/>
  <path d="M256 151V374" stroke="#14b8a6" stroke-width="10" stroke-linecap="round"/>
  <path d="M133 188Q173 181 218 198M133 226Q173 219 218 236M133 264Q173 257 209 270" fill="none" stroke="#94a3b8" stroke-width="10" stroke-linecap="round"/>
  <path d="M300 188Q337 177 377 184M300 226Q337 215 377 222" fill="none" stroke="#94a3b8" stroke-width="10" stroke-linecap="round"/>
  <circle cx="365" cy="369" r="93" fill="#0f172a"/>
  <circle cx="365" cy="369" r="79" fill="#fbbf24"/>
  <circle cx="365" cy="369" r="62" fill="#fffbeb"/>
  <path d="M365 318V328M416 369H406M365 420V410M314 369H324" stroke="#d97706" stroke-width="6" stroke-linecap="round"/>
  <path d="M365 338V369L389 384" fill="none" stroke="#0f172a" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="365" cy="369" r="7" fill="#0f766e"/>
</svg>\n`;
await writeFile(path.join(assets, 'logo.svg'), svg);
await sharp(Buffer.from(svg)).resize(512, 512).png({ compressionLevel: 9 }).toFile(path.join(assets, 'logo.png'));
await sharp(Buffer.from(svg)).resize(128, 128).png({ compressionLevel: 9 }).toFile(path.join(assets, 'icon.png'));
console.log(JSON.stringify({ logo: '512x512', composerIcon: '128x128', generated: true }));
