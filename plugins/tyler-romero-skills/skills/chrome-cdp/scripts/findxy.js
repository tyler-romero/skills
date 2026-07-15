// Find a visible element by its text and return its CSS-pixel center (ready to pass to `cdp.js click`).
// Usage: node findxy.js <targetId> "<text to find>" [--all]
// Prints JSON: {found, x, y, tag, text} for the smallest visible element whose text contains the needle
// (case-insensitive). With --all, prints up to 20 matches. Coords are viewport-relative CSS px.
const PORT = process.env.CDP_PORT || 9222;
(async () => {
  const targetId = process.argv[2];
  const needle = process.argv[3] || '';
  const all = process.argv.includes('--all');
  const targets = await (await fetch(`http://localhost:${PORT}/json`)).json();
  const t = targets.find(x => x.id === targetId) || targets.find(x => x.type === 'page');
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const mid = ++id; pend.set(mid, { res, rej }); ws.send(JSON.stringify({ id: mid, method, params })); });
  const race = (p, ms) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error('eval-timeout')), ms))]);
  // Build the page expression. JSON.stringify safely escapes the needle into the source.
  const expr = `(() => {
    const needle = ${JSON.stringify(needle)}.toLowerCase();
    const all = ${all};
    const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 2 && r.height > 2 && s.visibility !== 'hidden' && s.display !== 'none' && r.bottom > 0 && r.top < innerHeight + 4 && r.right > 0 && r.left < innerWidth + 4; };
    const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    const hits = [];
    for (const el of document.querySelectorAll('*')) {
      if (!vis(el)) continue;
      const o = own(el);
      const txt = (o || el.innerText || el.getAttribute('aria-label') || '').trim();
      if (!txt) continue;
      if (!txt.toLowerCase().includes(needle)) continue;
      const r = el.getBoundingClientRect();
      hits.push({ x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2), tag: el.tagName.toLowerCase(), text: txt.slice(0, 50), area: r.width * r.height, exact: o.toLowerCase() === needle });
    }
    // Prefer exact own-text matches, then smallest area (most specific element).
    hits.sort((a, b) => (b.exact - a.exact) || (a.area - b.area));
    if (!hits.length) return { found: false };
    if (all) return { found: true, count: hits.length, matches: hits.slice(0, 20).map(({ area, ...h }) => h) };
    const { area, ...best } = hits[0];
    return { found: true, ...best };
  })()`;
  try {
    const r = await race(send('Runtime.evaluate', { expression: expr, returnByValue: true }), 12000);
    if (r.exceptionDetails) console.log('EXC ' + JSON.stringify(r.exceptionDetails).slice(0, 300));
    else console.log(JSON.stringify(r.result && r.result.value));
  } catch (e) { console.log('ERR ' + e.message); }
  ws.close(); process.exit(0);
})().catch(e => { console.log('FATAL ' + e.message); process.exit(1); });
