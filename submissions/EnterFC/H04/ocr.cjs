// Real local OCR. Language models are pinned npm dependencies; no remote API.
const fs = require('node:fs');
const path = require('node:path');
const { createWorker } = require('tesseract.js');

async function main() {
  const cache = path.join(__dirname, '.cache', 'tessdata');
  fs.mkdirSync(cache, { recursive: true });
  for (const lang of ['rus', 'eng']) {
    const data = require(`@tesseract.js-data/${lang}`);
    fs.copyFileSync(path.join(data.langPath, `${lang}.traineddata.gz`),
      path.join(cache, `${lang}.traineddata.gz`));
  }
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const worker = await createWorker((process.argv[3] || 'rus+eng').split('+'), 1,
    { langPath: cache, cachePath: cache });
  try {
    for (const job of jobs) {
      await worker.setParameters({ tessedit_pageseg_mode: String(job.psm) });
      const { data } = await worker.recognize(job.image, {}, { text: true, tsv: true, blocks: true });
      fs.writeFileSync(job.output, JSON.stringify(data, null, 2) + '\n', 'utf8');
      console.log(`${path.basename(job.image)} confidence=${data.confidence}`);
    }
  } finally {
    await worker.terminate();
  }
}
main().catch(error => { console.error(error.stack); process.exitCode = 1; });
