import puppeteer from "puppeteer-core";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://localhost:5173";
const ARTIFACT_DIR = "C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\ed4d7401-a662-46f8-9f5c-a8580457e698";

const VIEWPORTS = [
  { name: "desktop_1440", width: 1440, height: 900, isMobile: false },
  { name: "laptop_1280", width: 1280, height: 800, isMobile: false },
  { name: "tablet_768", width: 768, height: 1024, isMobile: false },
  { name: "mobile_390", width: 390, height: 844, isMobile: true },
  { name: "mobile_360", width: 360, height: 780, isMobile: true },
];

async function capture() {
  console.log("Launching headless browser for responsive hero verification...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage();

  for (const vp of VIEWPORTS) {
    console.log(`Setting viewport: ${vp.name} (${vp.width}x${vp.height})...`);
    await page.setViewport({ width: vp.width, height: vp.height, isMobile: vp.isMobile });
    await page.goto(`${BASE_URL}/#/`, { waitUntil: "networkidle0" });
    await new Promise((r) => setTimeout(r, 600));

    // Check if horizontal scrollbar / overflow exists
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    const hasHorizontalOverflow = scrollWidth > clientWidth;
    console.log(`   Overflow check: scrollWidth=${scrollWidth}, clientWidth=${clientWidth}, overflow=${hasHorizontalOverflow}`);
    if (hasHorizontalOverflow) {
      console.warn(`⚠️ Horizontal overflow detected at ${vp.name}!`);
    }

    const screenshotPath = path.join(ARTIFACT_DIR, `hero_${vp.name}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`   Saved screenshot: hero_${vp.name}.png`);
  }

  await browser.close();
  console.log("\n✅ Responsive verification complete!");
}

capture().catch((err) => {
  console.error("Error capturing responsive hero:", err);
  process.exit(1);
});
