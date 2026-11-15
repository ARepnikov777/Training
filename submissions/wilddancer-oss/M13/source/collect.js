// Collector for M13. Run in the browser console (or Playwright browser_evaluate)
// on http://127.0.0.1:8765/catalog?category=laptop
// It walks every pagination link, then opens each product card and reads its fields.
// Returns {count, pages, rows, csv}.
async () => {
  const FIELDS = ['id', 'name', 'category', 'price', 'currency', 'supplier',
    'availability', 'ram_GB', 'ssd_GB', 'screen_inches', 'source_url'];
  const load = async (url) => {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${r.status} on ${url}`);
    return new DOMParser().parseFromString(await r.text(), 'text/html');
  };
  const start = new URL('/catalog?category=laptop', location.origin).href;
  const first = await load(start);
  const count = Number(first.getElementById('count').textContent);
  const pages = [...first.querySelectorAll('nav[aria-label="Страницы"] a')]
    .map((a) => new URL(a.getAttribute('href'), location.origin).href);

  const links = [];
  for (const p of pages) {
    const doc = await load(p);
    for (const a of doc.querySelectorAll('table a[href^="/product"]')) {
      links.push({page: p, url: new URL(a.getAttribute('href'), location.origin).href});
    }
  }

  const rows = [];
  for (const {url} of links) {
    const doc = await load(url);
    const dts = [...doc.querySelectorAll('dl dt')];
    const rec = {};
    for (const dt of dts) rec[dt.textContent] = dt.nextElementSibling.textContent;
    const row = {};
    for (const f of FIELDS) {
      const v = rec[f];
      row[f] = v === undefined || v === 'None' ? '' : v; // missing -> empty
    }
    row.source_url = url;
    rows.push(row);
  }

  const esc = (v) => (/[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
  const csv = [FIELDS.join(','), ...rows.map((r) => FIELDS.map((f) => esc(String(r[f]))).join(','))].join('\n') + '\n';
  return {count, pages, linkCount: links.length, rows, csv};
}
