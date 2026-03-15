import { readdir, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = path.resolve(__dirname, '..');
const inputDir = path.join(projectRoot, 'public', 'agent');
const outputDir = path.join(projectRoot, 'src', 'generated');
const outputFile = path.join(outputDir, 'agentPublicIcons.js');

const isSvg = (name) => /\.svg$/i.test(name);

const toPublicUrl = (filename) => `/agent/${filename}`;

const run = async () => {
  let files = [];
  try {
    files = await readdir(inputDir, { withFileTypes: true });
  } catch {
    files = [];
  }

  const icons = files
    .filter((d) => d.isFile() && isSvg(d.name))
    .map((d) => d.name)
    .sort((a, b) => a.localeCompare(b))
    .map(toPublicUrl);

  await mkdir(outputDir, { recursive: true });

  const content =
    `export const agentPublicSvgIcons = ${JSON.stringify(icons, null, 2)};\n` +
    `export default agentPublicSvgIcons;\n`;

  await writeFile(outputFile, content, 'utf8');
};

run();
