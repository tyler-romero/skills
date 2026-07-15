// Minimal dependency-free CDP driver for Chrome (remote debugging on :9222)
// Usage:
//   node cdp.js targets
//   node cdp.js setdl  <downloadDir>
//   node cdp.js shot   <targetId|-> <out.png>
//   node cdp.js nav    <targetId|-> <url>
//   node cdp.js pdf    <targetId|-> <out.pdf>
//   node cdp.js savemail <targetId|-> <out.html>
//   node cdp.js eval   <targetId|-> <jsfile>      (JS file; returnByValue JSON printed)
//   node cdp.js click  <targetId|-> <x> <y>       (CSS px, viewport-relative)
//   node cdp.js chooserupload <targetId|-> <x> <y> <file>
//   node cdp.js filecount <targetId|->
//   node cdp.js setfile <targetId|-> <file> [idx]
//   node cdp.js wheel  <targetId|-> <x> <y> [dy]
//   node cdp.js type   <targetId|-> <text>
//   node cdp.js key    <targetId|-> <Enter|Tab|Escape|Backspace>
const fs = require('fs');
const PORT = process.env.CDP_PORT || 9222;
const BASE = `http://localhost:${PORT}`;

async function listTargets() {
  const r = await fetch(`${BASE}/json`);
  return await r.json();
}
async function pageWs(targetId) {
  const targets = await listTargets();
  let t = (!targetId || targetId === '-')
    ? targets.find(x => x.type === 'page')
    : targets.find(x => x.id === targetId);
  if (!t) throw new Error('no page target found');
  return t.webSocketDebuggerUrl;
}
function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => resolve(ws);
    ws.onerror = (e) => reject(new Error('ws error: ' + (e.message || e)));
  });
}
function makeSender(ws) {
  let id = 0;
  const pending = new Map();
  const listeners = [];
  const rejectPending = (err) => {
    for (const { reject } of pending.values()) reject(err);
    pending.clear();
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    } else if (msg.method) {
      for (const l of listeners) l(msg);
    }
  };
  ws.onclose = () => rejectPending(new Error('ws closed'));
  ws.onerror = (e) => rejectPending(new Error('ws error: ' + (e.message || e.type || e)));
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    if (ws.readyState !== WebSocket.OPEN) {
      reject(new Error('ws is not open'));
      return;
    }
    const mid = ++id;
    pending.set(mid, { resolve, reject });
    try {
      ws.send(JSON.stringify({ id: mid, method, params }));
    } catch (e) {
      pending.delete(mid);
      reject(e);
    }
  });
  const onEvent = (fn) => listeners.push(fn);
  return { send, onEvent };
}
function waitEvent(api, method, timeoutMs = 30000) {
  return new Promise((resolve) => {
    const to = setTimeout(() => resolve({ __timeout: true }), timeoutMs);
    api.onEvent((m) => { if (m.method === method) { clearTimeout(to); resolve(m.params); } });
  });
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function main() {
  const [, , cmd, ...rest] = process.argv;
  if (cmd === 'targets') {
    const t = await listTargets();
    console.log(JSON.stringify(
      t.filter(x => x.type === 'page' || x.type === 'background_page')
       .map(x => ({ id: x.id, type: x.type, title: x.title, url: x.url })), null, 2));
    return;
  }
  if (cmd === 'setdl') {
    const dlPath = rest[0];
    const ver = await (await fetch(`${BASE}/json/version`)).json();
    const ws = await connect(ver.webSocketDebuggerUrl);
    const api = makeSender(ws);
    await api.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dlPath, eventsEnabled: true });
    console.log('download behavior -> ' + dlPath);
    ws.close(); return;
  }
  const targetId = rest[0];
  const wsUrl = await pageWs(targetId);
  const ws = await connect(wsUrl);
  const api = makeSender(ws);
  await api.send('Page.enable');
  await api.send('Runtime.enable');

  if (cmd === 'shot') {
    const out = rest[1] || 'shot.png';
    const r = await api.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(out, Buffer.from(r.data, 'base64'));
    const dim = await api.send('Runtime.evaluate', {
      expression: '({w:innerWidth,h:innerHeight,dpr:devicePixelRatio,url:location.href,title:document.title})',
      returnByValue: true });
    console.log('saved ' + out + ' ' + JSON.stringify(dim.result.value));
  } else if (cmd === 'nav') {
    const url = rest[1];
    const loaded = waitEvent(api, 'Page.loadEventFired', 45000);
    await api.send('Page.navigate', { url });
    await loaded;
    await sleep(800);
    const r = await api.send('Runtime.evaluate', {
      expression: '({u:location.href,t:document.title})', returnByValue: true });
    console.log(JSON.stringify(r.result.value));
  } else if (cmd === 'pdf') {
    const out = rest[1] || 'out.pdf';
    const r = await api.send('Page.printToPDF', { printBackground: true, preferCSSPageSize: true });
    fs.writeFileSync(out, Buffer.from(r.data, 'base64'));
    console.log('saved ' + out + ' (' + Buffer.from(r.data, 'base64').length + ' bytes)');
  } else if (cmd === 'savemail') {
    // Save the currently-open Gmail message body as a clean standalone HTML file (no context bloat)
    const out = rest[1] || 'mail.html';
    const r = await api.send('Runtime.evaluate', {
      expression: "(()=>{const b=document.querySelector('.a3s');return b?b.outerHTML:'';})()",
      returnByValue: true });
    const inner = r.result.value || '';
    if (!inner) { console.log('NO_BODY'); ws.close(); return; }
    const html = '<!doctype html><html><head><meta charset="utf-8">' +
      '<style>body{font-family:Arial,Helvetica,sans-serif;margin:28px;color:#111;} img{max-width:100%;height:auto;}</style>' +
      '</head><body>' + inner + '</body></html>';
    fs.writeFileSync(out, html);
    console.log('saved ' + out + ' (' + Buffer.byteLength(html) + ' bytes)');
  } else if (cmd === 'eval') {
    const expr = fs.readFileSync(rest[1], 'utf8');
    const r = await api.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) console.log('EXCEPTION: ' + JSON.stringify(r.exceptionDetails));
    else console.log(JSON.stringify(r.result.value));
  } else if (cmd === 'click') {
    const x = Number(rest[1]), y = Number(rest[2]);
    await api.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await api.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await api.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    console.log('clicked ' + x + ',' + y);
  } else if (cmd === 'chooserupload') {
    const x = Number(rest[1]), y = Number(rest[2]);
    const file = rest[3];
    await api.send('DOM.enable');
    await api.send('Page.setInterceptFileChooserDialog', { enabled: true });
    let backend = null;
    const got = new Promise((resolve) => { api.onEvent(m => { if (m.method === 'Page.fileChooserOpened') { backend = m.params.backendNodeId; resolve(m.params); } }); });
    await api.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await api.send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await api.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    await Promise.race([got, new Promise(r => setTimeout(() => r(null), 8000))]);
    if (!backend) { console.log('NO_CHOOSER_EVENT'); }
    else {
      await api.send('DOM.setFileInputFiles', { files: [file], backendNodeId: backend });
      console.log('uploaded ' + file.split('/').pop() + ' (backendNodeId=' + backend + ')');
    }
    await api.send('Page.setInterceptFileChooserDialog', { enabled: false });
  } else if (cmd === 'filecount') {
    const doc = await api.send('DOM.getDocument', { depth: -1, pierce: true });
    const qs = await api.send('DOM.querySelectorAll', { nodeId: doc.root.nodeId, selector: 'input[type=file]' });
    console.log('file inputs: ' + ((qs.nodeIds || []).length));
  } else if (cmd === 'setfile') {
    const file = rest[1];
    const idx = Number(rest[2] || 0);
    const doc = await api.send('DOM.getDocument', { depth: -1, pierce: true });
    const qs = await api.send('DOM.querySelectorAll', { nodeId: doc.root.nodeId, selector: 'input[type=file]' });
    const ids = qs.nodeIds || [];
    if (!ids.length) { console.log('NO_FILE_INPUT'); }
    else {
      const useIdx = Math.min(idx, ids.length - 1);
      await api.send('DOM.setFileInputFiles', { files: [file], nodeId: ids[useIdx] });
      console.log('set file on input ' + useIdx + ' of ' + ids.length);
    }
  } else if (cmd === 'wheel') {
    const x = Number(rest[1]), y = Number(rest[2]), dy = Number(rest[3] || 600);
    await api.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
    await api.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x, y, deltaX: 0, deltaY: dy });
    console.log('wheel dy=' + dy + ' at ' + x + ',' + y);
  } else if (cmd === 'type') {
    await api.send('Input.insertText', { text: rest[1] });
    console.log('typed');
  } else if (cmd === 'key') {
    const map = {
      Enter: { keyCode: 13, key: 'Enter', code: 'Enter', text: '\r' },
      Tab: { keyCode: 9, key: 'Tab', code: 'Tab' },
      Escape: { keyCode: 27, key: 'Escape', code: 'Escape' },
      Backspace: { keyCode: 8, key: 'Backspace', code: 'Backspace' },
    };
    const k = map[rest[1]] || { key: rest[1] };
    await api.send('Input.dispatchKeyEvent', { type: 'keyDown', ...k });
    await api.send('Input.dispatchKeyEvent', { type: 'keyUp', ...k });
    console.log('key ' + rest[1]);
  } else {
    console.log('unknown cmd: ' + cmd);
  }
  ws.close();
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
