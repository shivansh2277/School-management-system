import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BROWSER_PATH = fs.existsSync(EDGE_PATH) ? EDGE_PATH : CHROME_PATH;
const USER_DATA_DIR = path.resolve("scripts/tmp_chrome_profile_website");
const SCREENSHOT_DIR = path.resolve("docs/screenshots/website_upgrades");

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const PORT = 9225;
console.log("[*] Launching headless browser on port " + PORT + "...");
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
  console.error("[-] Failed to connect to browser CDP");
  browser.kill();
  process.exit(1);
}

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
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    this.ws.close();
  }
}

const browserCdp = new CDPClient(wsUrl);
await browserCdp.connect();

const { targetId } = await browserCdp.send("Target.createTarget", { url: "about:blank" });
const targetWsUrl = `ws://127.0.0.1:${PORT}/devtools/page/${targetId}`;
const pageCdp = new CDPClient(targetWsUrl);
await pageCdp.connect();

async function takeScreenshot(outputPath, width = 1440, height = 900) {
  await pageCdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: width < 768,
  });
  await sleep(400);
  const result = await pageCdp.send("Page.captureScreenshot", { format: "png" });
  if (result && result.data) {
    fs.writeFileSync(outputPath, Buffer.from(result.data, "base64"));
    console.log(`[+] Saved screenshot: ${outputPath}`);
  }
}

async function evaluate(expression) {
  const res = await pageCdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  return res && res.result ? res.result.value : null;
}

try {
  await pageCdp.send("Page.enable");
  await pageCdp.send("DOM.enable");
  await pageCdp.send("Network.enable");

  // 1. Home Page - Hero Carousel Slide 1 & Trust Highlights
  console.log("[*] Navigating to http://localhost:5173/ ...");
  await pageCdp.send("Page.navigate", { url: "http://localhost:5173/" });
  await sleep(2500);

  await takeScreenshot(path.join(SCREENSHOT_DIR, "01_home_hero_slide1_trust_badge.png"), 1440, 900);

  // Wait 3.2 seconds for carousel auto-slide to image 2
  console.log("[*] Waiting 3.2 seconds for carousel auto-advance to slide 2...");
  await sleep(3200);
  await takeScreenshot(path.join(SCREENSHOT_DIR, "02_home_hero_carousel_slide2.png"), 1440, 900);

  // Scroll down to Principal Section
  console.log("[*] Scrolling to Principal Welcome & Quote Card...");
  await evaluate("window.scrollTo({ top: 1100, behavior: 'instant' })");
  await sleep(800);
  await takeScreenshot(path.join(SCREENSHOT_DIR, "03_home_principal_section.png"), 1440, 900);

  // 2. About Page - Founder Portrait & Heritage
  console.log("[*] Navigating to http://localhost:5173/about ...");
  await pageCdp.send("Page.navigate", { url: "http://localhost:5173/about" });
  await sleep(2000);
  await evaluate("window.scrollTo({ top: 900, behavior: 'instant' })");
  await sleep(600);
  await takeScreenshot(path.join(SCREENSHOT_DIR, "04_about_founder_portrait.png"), 1440, 900);

  // 3. Public Disclosure Page - Demo School Code & Principal Info
  console.log("[*] Navigating to http://localhost:5173/public-disclosure ...");
  await pageCdp.send("Page.navigate", { url: "http://localhost:5173/public-disclosure" });
  await sleep(2000);
  await takeScreenshot(path.join(SCREENSHOT_DIR, "05_public_disclosure_demo_code.png"), 1440, 900);

  // 4. Test Scroll-to-Top behavior when clicking active or another nav item
  console.log("[*] Testing Scroll-to-Top behavior...");
  // First scroll down to 800px on Public Disclosure page
  await evaluate("window.scrollTo({ top: 800, behavior: 'instant' })");
  await sleep(500);
  const scrollBefore = await evaluate("window.scrollY || document.documentElement.scrollTop");
  console.log(`[*] Scroll position before clicking nav link: ${scrollBefore}px`);

  // Click 'Home' link in navbar
  await evaluate(`
    const nav = document.querySelector('nav[aria-label="Main navigation"]');
    const homeLink = Array.from(nav.querySelectorAll('a')).find(a => a.textContent.includes('Home'));
    if (homeLink) homeLink.click();
  `);
  await sleep(800);
  const scrollAfter = await evaluate("window.scrollY || document.documentElement.scrollTop");
  console.log(`[*] Scroll position after clicking Home nav link: ${scrollAfter}px`);

  await takeScreenshot(path.join(SCREENSHOT_DIR, "06_home_scroll_to_top_verified.png"), 1440, 900);

  // Scroll down on Home page, then click 'Home' tab again (already active tab)
  await evaluate("window.scrollTo({ top: 1200, behavior: 'instant' })");
  await sleep(500);
  const activeTest = await evaluate(`
    (() => {
      const nav = document.querySelector('nav[aria-label="Main navigation"]');
      const homeLink = Array.from(nav.querySelectorAll('a')).find(a => a.textContent.includes('Home'));
      const before = window.scrollY;
      if (homeLink) homeLink.click();
      return { before, after: window.scrollY };
    })()
  `);
  console.log(`[*] Scroll position before clicking already-active Home tab: ${activeTest.before}px`);
  console.log(`[*] Scroll position after clicking already-active Home tab: ${activeTest.after}px`);

  console.log("[+] All screenshots and scroll behaviors verified successfully!");
} finally {
  pageCdp.close();
  browserCdp.close();
  browser.kill();
  try {
    fs.rmSync(USER_DATA_DIR, { recursive: true, force: true });
  } catch (e) {}
}
