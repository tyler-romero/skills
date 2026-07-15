// Safe screenshot with hard timeout and non-confirming JS dialog dismissal.
const fs = require('fs');
const PORT = process.env.CDP_PORT || 9222;
(async () => {
  const targets = await (await fetch(`http://localhost:${PORT}/json`)).json();
  const t = targets.find(x => x.id === process.argv[2]) || targets.find(x => x.type === 'page');
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const mid = ++id; pend.set(mid, { res, rej }); ws.send(JSON.stringify({ id: mid, method, params })); });
  const race = (p, ms, label) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error(label || 'timeout')), ms))]);
  try { await race(send('Page.handleJavaScriptDialog', { accept: false }), 3000, 'no-dialog'); console.log('dismissed a dialog'); } catch (e) { /* no dialog */ }
  try {
    const r = await race(send('Page.captureScreenshot', { format: 'png' }), 15000, 'screenshot-timeout');
    fs.writeFileSync(process.argv[3], Buffer.from(r.data, 'base64'));
    console.log('saved ' + process.argv[3]);
  } catch (e) { console.log('SHOT_ERR ' + e.message); }
  ws.close();
  process.exit(0);
})().catch(e => { console.log('FATAL ' + e.message); process.exit(1); });
