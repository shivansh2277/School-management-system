import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BROWSER_PATH = fs.existsSync(EDGE_PATH) ? EDGE_PATH : CHROME_PATH;
const USER_DATA_DIR = path.resolve("scripts/tmp_chrome_profile");
const SCREENSHOT_DIR = path.resolve("docs/screenshots");

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// 1. Authenticate to get admin token
console.log("[*] Authenticating as admin@sunrisepublic.edu...");
const authRes = await fetch("http://127.0.0.1:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    role: "admin",
    login_id: "admin@sunrisepublic.edu",
    password: "Admin@123",
  }),
});
const authData = await authRes.json();
const token = authData.access_token;
const refresh = authData.refresh_token;
console.log("[*] Authenticated successfully. User:", authData.user.full_name);

// 2. Launch Headless Browser
const PORT = 9222;
console.log("[*] Launching headless browser with CDP on port " + PORT + "...");
const browser = spawn(
  BROWSER_PATH,
  [
    `--remote-debugging-port=${PORT}`,
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    `--user-data-dir=${USER_DATA_DIR}`,
    "about:blank",
  ],
  { stdio: "ignore" }
);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let wsUrl = null;
for (let i = 0; i < 30; i++) {
  await sleep(300);
  try {
    const vRes = await fetch(`http://127.0.0.1:${PORT}/json/version`);
    const vData = await vRes.json();
    wsUrl = vData.webSocketDebuggerUrl;
    if (wsUrl) break;
  } catch (e) {}
}

if (!wsUrl) {
  browser.kill();
  throw new Error("Could not connect to browser CDP");
}
console.log("[*] Connected to browser CDP:", wsUrl);

class CDPClient {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.id = 0;
    this.callbacks = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id && this.callbacks.has(msg.id)) {
          const { resolve, reject } = this.callbacks.get(msg.id);
          this.callbacks.delete(msg.id);
          if (msg.error) reject(msg.error);
          else resolve(msg.result);
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    this.ws.close();
  }
}

const cdp = new CDPClient(wsUrl);
await cdp.connect();

const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
const targetWsUrl = `ws://127.0.0.1:${PORT}/devtools/page/${targetId}`;
const pageCdp = new CDPClient(targetWsUrl);
await pageCdp.connect();

await pageCdp.send("Page.enable");
await pageCdp.send("Runtime.enable");
await pageCdp.send("DOM.enable");

async function setViewport(width, height) {
  await pageCdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 2,
    mobile: width < 768,
  });
}

async function capture(filePath) {
  const { data } = await pageCdp.send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(filePath, Buffer.from(data, "base64"));
  console.log(`[+] Captured: ${filePath}`);
}

async function waitForText(text, maxTries = 30) {
  for (let i = 0; i < maxTries; i++) {
    const res = await pageCdp.send("Runtime.evaluate", {
      expression: `document.body.innerText.includes(${JSON.stringify(text)})`,
      returnByValue: true,
    });
    if (res?.result?.value) return true;
    await sleep(400);
  }
  return false;
}

// Navigate and set token
await setViewport(1440, 900);
await pageCdp.send("Page.navigate", { url: "http://localhost:5173/" });
await sleep(1500);

await pageCdp.send("Runtime.evaluate", {
  expression: `
    localStorage.setItem('sunrise.token', ${JSON.stringify(token)});
    localStorage.setItem('sunrise.refresh', ${JSON.stringify(refresh)});
  `,
});

// Navigate to dashboard
console.log("[*] Navigating to http://localhost:5173/#/dashboard...");
await pageCdp.send("Page.navigate", { url: "http://localhost:5173/#/dashboard" });

// Wait until "Total Students" is rendered
console.log("[*] Waiting for dashboard data to load...");
await waitForText("Total Students");
await sleep(1000);

// 1. Desktop Screenshot (1440x900)
console.log("[*] Capturing Desktop...");
await setViewport(1440, 900);
await sleep(500);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_desktop.png"));

// 2. Desktop Full Page Screenshot
console.log("[*] Capturing Desktop Full Page...");
await setViewport(1440, 1300);
await sleep(500);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_desktop_fullpage.png"));

// 3. Laptop Screenshot (1024x768)
console.log("[*] Capturing Laptop...");
await setViewport(1024, 768);
await sleep(500);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_laptop.png"));

// 4. Tablet Screenshot (768x1024)
console.log("[*] Capturing Tablet...");
await setViewport(768, 1024);
await sleep(500);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_tablet.png"));

// Reset to Desktop for modal verifications
await setViewport(1440, 900);
await sleep(500);

// 5. Test Defaulters Modal
console.log("[*] Opening Defaulters modal...");
await pageCdp.send("Runtime.evaluate", {
  expression: `
    const allButtons = Array.from(document.querySelectorAll('button, a'));
    const btn = allButtons.find(b => b.innerText && b.innerText.includes('View Roster'));
    if (btn) btn.click();
  `,
});
await waitForText("Pending Fee Students");
await sleep(800);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_defaulters_modal.png"));

// Close Defaulters modal
console.log("[*] Closing Defaulters modal...");
await pageCdp.send("Runtime.evaluate", {
  expression: `
    const closeBtn = document.querySelector('button[aria-label="Close"]');
    if (closeBtn) closeBtn.click();
  `,
});
await sleep(1000);

// 6. Test Grievances Inspection Modal
console.log("[*] Opening Grievances Inspection modal...");
const clickResult = await pageCdp.send("Runtime.evaluate", {
  expression: `(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const inspectBtn = btns.find(b => b.textContent && !b.textContent.includes('Defaulters') && (b.textContent.includes('Inspect') || b.textContent.includes('replies')));
    if (inspectBtn) {
      inspectBtn.click();
      return "Clicked inspect button: " + inspectBtn.textContent;
    }
    return "Inspect button not found! Total buttons: " + btns.length;
  })()`,
  returnByValue: true,
});
console.log("[*] Click result:", clickResult?.result?.value);
const hasGrievanceModal = await waitForText("Issue Description");
console.log("[*] Grievance modal loaded:", hasGrievanceModal);
await sleep(1200);
await capture(path.join(SCREENSHOT_DIR, "admin_dashboard_upgrade_grievance_modal.png"));

console.log("[*] All screenshots and modal verifications completed!");
pageCdp.close();
cdp.close();
browser.kill();
process.exit(0);
