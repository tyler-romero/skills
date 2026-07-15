// safe Runtime.evaluate with hard timeout. usage: node safeeval.js <targetId> <jsfile>
const fs = require('fs');
const PORT = process.env.CDP_PORT || 9222;
(async () => {
  const targets = await (await fetch(`http://localhost:${PORT}/json`)).json();
  const t = targets.find(x => x.id === process.argv[2]) || targets.find(x => x.type === 'page');
  const expr = fs.readFileSync(process.argv[3], 'utf8');
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const mid = ++id; pend.set(mid, { res, rej }); ws.send(JSON.stringify({ id: mid, method, params })); });
  const race = (p, ms) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error('eval-timeout')), ms))]);
  try {
    const r = await race(send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }), 12000);
    if (r.exceptionDetails) console.log('EXC ' + JSON.stringify(r.exceptionDetails).slice(0, 300));
    else console.log(JSON.stringify(r.result && r.result.value));
  } catch (e) { console.log('EVAL_ERR ' + e.message); }
  ws.close(); process.exit(0);
})().catch(e => { console.log('FATAL ' + e.message); process.exit(1); });
