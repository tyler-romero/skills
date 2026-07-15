#!/usr/bin/env node

// Launch or reuse a dedicated Chrome profile with loopback CDP enabled.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const port = Number(process.env.CDP_PORT || 9222);
const profile = path.resolve(
  process.env.CHROME_CDP_PROFILE || path.join(os.homedir(), '.chrome-cdp-profile'),
);
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const urlIndex = args.indexOf('--url');
const initialUrl = urlIndex >= 0 ? args[urlIndex + 1] : 'about:blank';

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error(`invalid CDP_PORT: ${process.env.CDP_PORT}`);
}
if (!initialUrl || !/^(https?:\/\/|about:blank$)/i.test(initialUrl)) {
  throw new Error('--url must be an http(s) URL or about:blank');
}

const endpoint = `http://localhost:${port}/json/version`;

async function endpointStatus() {
  try {
    const response = await fetch(endpoint, { signal: AbortSignal.timeout(1000) });
    if (!response.ok) return null;
    const data = await response.json();
    return data.Browser ? data : null;
  } catch {
    return null;
  }
}

function executableOnPath(name) {
  const pathEntries = (process.env.PATH || '').split(path.delimiter);
  for (const entry of pathEntries) {
    const candidate = path.join(entry, name);
    try {
      fs.accessSync(candidate, fs.constants.X_OK);
      return candidate;
    } catch {
      // Try the next PATH entry.
    }
  }
  return null;
}

function launchSpec() {
  const chromeArgs = [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    initialUrl,
  ];

  if (process.platform === 'darwin') {
    return {
      command: '/usr/bin/open',
      args: ['-na', 'Google Chrome', '--args', ...chromeArgs],
    };
  }

  if (process.platform === 'win32') {
    const roots = [
      process.env.PROGRAMFILES,
      process.env['PROGRAMFILES(X86)'],
      process.env.LOCALAPPDATA,
    ].filter(Boolean);
    const executable = roots
      .map(root => path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'))
      .find(fs.existsSync);
    if (!executable) throw new Error('Google Chrome executable not found');
    return { command: executable, args: chromeArgs };
  }

  const executable = [
    'google-chrome',
    'google-chrome-stable',
    'chromium',
    'chromium-browser',
  ].map(executableOnPath).find(Boolean);
  if (!executable) throw new Error('Google Chrome or Chromium executable not found');
  return { command: executable, args: chromeArgs };
}

async function main() {
  const existing = await endpointStatus();
  if (existing) {
    if (!/(Chrome|Chromium)/i.test(existing.Browser)) {
      throw new Error(`CDP port ${port} is already used by ${existing.Browser}`);
    }
    console.log(JSON.stringify({
      status: 'ready',
      browser: existing.Browser,
      port,
      profile,
      reused: true,
    }));
    return;
  }

  const spec = launchSpec();
  if (dryRun) {
    console.log(JSON.stringify({
      status: 'dry-run',
      command: spec.command,
      args: spec.args,
      port,
      profile,
    }, null, 2));
    return;
  }

  const child = spawn(spec.command, spec.args, {
    detached: true,
    stdio: 'ignore',
    windowsHide: false,
  });
  child.unref();

  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    await new Promise(resolve => setTimeout(resolve, 250));
    const status = await endpointStatus();
    if (status) {
      console.log(JSON.stringify({
        status: 'launched',
        browser: status.Browser,
        port,
        profile,
        reused: false,
      }));
      return;
    }
  }

  throw new Error(`Chrome launched but CDP did not become ready at ${endpoint}`);
}

main().catch(error => {
  console.error(`ERR ${error.message}`);
  process.exit(1);
});
