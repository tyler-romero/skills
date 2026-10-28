#!/usr/bin/env node
// Render one or more .excalidraw scenes (or a directory of .excalidraw files)
// to PNGs using @excalidraw/excalidraw@0.18.1 in headless Chrome.
//
// Works with local `puppeteer` / `puppeteer-core` if installed, or falls back
// automatically to a zero-dependency headless Chrome CDP session via Node's
// built-in WebSocket.
//
// Usage:
//   node render.mjs <in.excalidraw> [out.png]
//   node render.mjs path/to/foo.excalidraw path/to/foo-mobile.excalidraw
//   node render.mjs <frames_dir>
//
// Environment variables:
//   PADDING=16      Export padding in unscaled Excalidraw units (default: 16)
//   SCALE=1.5       Override scene.appState.exportScale (default: scene's exportScale or 1.5)
//   EXPORT_BG=0     Set to 1 to export with viewBackgroundColor instead of transparent (default: 0)
//   BG=#fef9ed      Optional hex background color (implies EXPORT_BG=1 when set)

import { execFileSync, spawn } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function importFromWorkspace(pkgName) {
  const searchDirs = [process.cwd(), import.meta.dirname];
  try {
    const commonGitDir = execFileSync("git", ["rev-parse", "--git-common-dir"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    if (commonGitDir) {
      searchDirs.push(path.resolve(commonGitDir, ".."));
    }
  } catch {
    // Ignore if not in a git repository
  }
  for (const dir of searchDirs) {
    try {
      const req = createRequire(path.join(dir, "package.json"));
      const resolved = req.resolve(pkgName);
      return await import(pathToFileURL(resolved).href);
    } catch {
      // Try next directory
    }
  }
  return await import(pkgName);
}

function findChromeExecutable() {
  const candidates = [process.env.CHROME_PATH].filter(Boolean);
  const cacheRoot = path.join(os.homedir(), ".cache", "puppeteer", "chrome");
  if (fs.existsSync(cacheRoot)) {
    for (const ver of fs.readdirSync(cacheRoot).sort().reverse()) {
      const verDir = path.join(cacheRoot, ver);
      if (!fs.statSync(verDir).isDirectory()) continue;
      for (const arch of fs.readdirSync(verDir)) {
        candidates.push(
          path.join(
            verDir,
            arch,
            "Google Chrome for Testing.app",
            "Contents",
            "MacOS",
            "Google Chrome for Testing",
          ),
          path.join(verDir, arch, "chrome"),
        );
      }
    }
  }
  candidates.push(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  );
  return candidates.find((p) => fs.existsSync(p));
}

async function launchDirectCdpSession() {
  const executablePath = findChromeExecutable();
  if (!executablePath) {
    throw new Error(
      "Could not find a Chrome/Chromium executable. Set CHROME_PATH or install Google Chrome.",
    );
  }
  const tmpProfile = fs.mkdtempSync(path.join(os.tmpdir(), "excal-cdp-"));
  const proc = spawn(
    executablePath,
    [
      "--headless=new",
      "--remote-debugging-port=0",
      `--user-data-dir=${tmpProfile}`,
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-gpu",
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );

  const wsBrowserUrl = await new Promise((resolve, reject) => {
    let stderr = "";
    const timer = setTimeout(() => {
      reject(new Error(`Timed out waiting for Chrome DevTools endpoint.\n${stderr}`));
    }, 15000);
    proc.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
      const match = stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) {
        clearTimeout(timer);
        resolve(match[1]);
      }
    });
    proc.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    proc.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`Chrome exited early with code ${code}.\n${stderr}`));
    });
  });

  const port = new URL(wsBrowserUrl).port;
  const targetsRes = await fetch(`http://127.0.0.1:${port}/json`);
  const targets = await targetsRes.json();
  const pageTarget = targets.find((t) => t.type === "page");
  if (!pageTarget?.webSocketDebuggerUrl) {
    proc.kill();
    throw new Error("Could not find a page target in headless Chrome.");
  }

  const ws = await new Promise((resolve, reject) => {
    const socket = new WebSocket(pageTarget.webSocketDebuggerUrl);
    socket.onopen = () => resolve(socket);
    socket.onerror = (err) => reject(new Error(`WebSocket error: ${err.message || err}`));
  });

  let nextId = 0;
  const pending = new Map();
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) {
        reject(new Error(JSON.stringify(msg.error)));
      } else {
        resolve(msg.result);
      }
    }
  };

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++nextId;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  return {
    async evaluate(fn, ...fnArgs) {
      const serializedArgs = fnArgs.map((a) => JSON.stringify(a)).join(", ");
      const expression = `(${fn.toString()})(${serializedArgs})`;
      const res = await send("Runtime.evaluate", {
        expression,
        awaitPromise: true,
        returnByValue: true,
      });
      if (res.exceptionDetails) {
        throw new Error(
          res.exceptionDetails.exception?.description ||
            res.exceptionDetails.text ||
            "Runtime.evaluate failed",
        );
      }
      return res.result?.value;
    },
    async close() {
      try {
        ws.close();
      } catch {
        // Ignore close errors
      }
      proc.kill();
      try {
        fs.rmSync(tmpProfile, { recursive: true, force: true });
      } catch {
        // Ignore cleanup errors
      }
    },
  };
}

async function launchSession() {
  for (const pkg of ["puppeteer", "puppeteer-core"]) {
    try {
      const mod = await importFromWorkspace(pkg);
      const launchOpts = { headless: true };
      if (pkg === "puppeteer-core") {
        const executablePath = findChromeExecutable();
        if (!executablePath) continue;
        launchOpts.executablePath = executablePath;
      }
      const browser = await mod.default.launch(launchOpts);
      const page = await browser.newPage();
      await page.setContent("<!doctype html><html><body></body></html>");
      return {
        evaluate: (fn, ...fnArgs) => page.evaluate(fn, ...fnArgs),
        close: () => browser.close(),
      };
    } catch {
      // Fall through to next option
    }
  }
  return await launchDirectCdpSession();
}

// Resolve CLI flags and pairs of [inPath, outPath]
const rawArgs = process.argv.slice(2);
let cliBg = null;
const args = [];
for (let i = 0; i < rawArgs.length; i++) {
  if (rawArgs[i] === "--bg" && i + 1 < rawArgs.length) {
    cliBg = rawArgs[++i];
  } else if (rawArgs[i].startsWith("--bg=")) {
    cliBg = rawArgs[i].slice("--bg=".length);
  } else {
    args.push(rawArgs[i]);
  }
}

if (args.length === 0) {
  console.error("Usage: node render.mjs [--bg <hex|transparent>] <in.excalidraw|dir> [out.png | more.excalidraw...]");
  process.exit(1);
}

const pairs = [];
if (
  args.length === 2 &&
  args[0].endsWith(".excalidraw") &&
  args[1].endsWith(".png")
) {
  pairs.push([args[0], args[1]]);
} else {
  for (const arg of args) {
    const stat = fs.statSync(arg);
    if (stat.isDirectory()) {
      const files = fs
        .readdirSync(arg)
        .filter((f) => f.endsWith(".excalidraw"))
        .sort();
      for (const f of files) {
        const full = path.join(arg, f);
        pairs.push([full, full.replace(/\.excalidraw$/, ".png")]);
      }
    } else if (arg.endsWith(".excalidraw")) {
      pairs.push([arg, arg.replace(/\.excalidraw$/, ".png")]);
    }
  }
}

const padding = Number(process.env.PADDING ?? 16);
const rawBg = (cliBg ?? process.env.BG ?? "").trim();
const isExplicitTransparent =
  rawBg.toLowerCase() === "transparent" || rawBg.toLowerCase() === "none";
const bgOverride = rawBg && !isExplicitTransparent ? rawBg : null;
const exportBg =
  !isExplicitTransparent &&
  (process.env.EXPORT_BG === "1" || Boolean(bgOverride));
const scaleOverride = process.env.SCALE ? Number(process.env.SCALE) : null;

const session = await launchSession();
await session.evaluate(async () => {
  window.__excal = await import(
    "https://esm.sh/@excalidraw/excalidraw@0.18.1?deps=react@19.1.0,react-dom@19.1.0"
  );
  await document.fonts.ready;
});

for (const [inPath, outPath] of pairs) {
  const scene = JSON.parse(fs.readFileSync(inPath, "utf8"));
  const scale = scaleOverride ?? scene.appState?.exportScale ?? 1.5;
  const b64 = await session.evaluate(
    async (scene, scale, padding, exportBg, bgOverride) => {
      const blob = await window.__excal.exportToBlob({
        elements: scene.elements,
        appState: {
          ...scene.appState,
          viewBackgroundColor:
            bgOverride || scene.appState?.viewBackgroundColor || "#ffffff",
          exportBackground: exportBg,
          exportScale: scale,
        },
        files: scene.files || {},
        exportPadding: padding,
        getDimensions: (w, h) => ({
          width: Math.round(w * scale),
          height: Math.round(h * scale),
          scale,
        }),
        mimeType: "image/png",
      });
      const buf = await blob.arrayBuffer();
      let bin = "";
      const bytes = new Uint8Array(buf);
      for (let i = 0; i < bytes.length; i++) {
        bin += String.fromCharCode(bytes[i]);
      }
      return btoa(bin);
    },
    scene,
    scale,
    padding,
    exportBg,
    bgOverride,
  );
  fs.writeFileSync(outPath, Buffer.from(b64, "base64"));
  console.log("wrote", outPath);
}

await session.close();
