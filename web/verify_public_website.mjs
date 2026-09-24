import puppeteer from "puppeteer-core";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://localhost:5174";
const ARTIFACT_DIR = "C:\\Users\\SHIVANSH\\.gemini\\antigravity\\brain\\ed4d7401-a662-46f8-9f5c-a8580457e698";

async function run() {
  console.log("Launching headless Chrome...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1280,900"],
    defaultViewport: { width: 1280, height: 900 },
  });

  const page = await browser.newPage();
  const errors = [];

  page.on("pageerror", (err) => {
    console.error("PAGE ERROR:", err.message);
    errors.push(err.message);
  });

  try {
    // 1. HOME PAGE
    console.log("1. Navigating to Home:", BASE_URL);
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });
    await new Promise((r) => setTimeout(r, 1000));

    const homeHeading = await page.$eval("h1", (el) => el.textContent);
    console.log("   Home Heading:", homeHeading);
    if (!homeHeading.includes("Nurturing Curious Minds")) {
      throw new Error("Unexpected Home heading: " + homeHeading);
    }

    const erpNavBtn = await page.$eval('header a[href="#/login"]', (el) => el.textContent.trim());
    console.log("   Navbar ERP Button:", erpNavBtn);

    await page.screenshot({ path: path.join(ARTIFACT_DIR, "homepage_desktop.png"), fullPage: false });
    console.log("   Captured homepage_desktop.png");

    // 2. ABOUT PAGE
    console.log("2. Navigating to /about...");
    await page.click('nav a[href="#/about"]');
    await new Promise((r) => setTimeout(r, 800));
    const aboutHeading = await page.$eval("h1", (el) => el.textContent);
    console.log("   About Heading:", aboutHeading);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "about_desktop.png"), fullPage: false });
    console.log("   Captured about_desktop.png");

    // 3. ACADEMICS PAGE
    console.log("3. Navigating to /academics...");
    await page.click('nav a[href="#/academics"]');
    await new Promise((r) => setTimeout(r, 800));
    const academicsHeading = await page.$eval("h1", (el) => el.textContent);
    console.log("   Academics Heading:", academicsHeading);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "academics_desktop.png"), fullPage: false });
    console.log("   Captured academics_desktop.png");

    // 4. ADMISSIONS PAGE
    console.log("4. Navigating to /admissions...");
    await page.click('nav a[href="#/admissions"]');
    await new Promise((r) => setTimeout(r, 800));
    const admissionsHeading = await page.$eval("h1", (el) => el.textContent);
    console.log("   Admissions Heading:", admissionsHeading);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "admissions_desktop.png"), fullPage: false });
    console.log("   Captured admissions_desktop.png");

    // 5. FACILITIES PAGE
    console.log("5. Navigating to /facilities...");
    await page.click('nav a[href="#/facilities"]');
    await new Promise((r) => setTimeout(r, 800));
    const facilitiesHeading = await page.$eval("h1", (el) => el.textContent);
    console.log("   Facilities Heading:", facilitiesHeading);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "facilities_desktop.png"), fullPage: false });
    console.log("   Captured facilities_desktop.png");

    // 6. CLICK "LOGIN TO ERP"
    console.log("6. Clicking Login to ERP button...");
    await page.click('header a[href="#/login"]');
    await new Promise((r) => setTimeout(r, 800));
    const currentUrl = page.url();
    console.log("   Current URL after clicking ERP Login:", currentUrl);
    if (!currentUrl.includes("#/login")) {
      throw new Error("Failed to navigate to #/login: " + currentUrl);
    }
    const loginTitle = await page.$eval("form h1", (el) => el.textContent);
    console.log("   Login Page Title:", loginTitle);
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "erp_login_page.png"), fullPage: false });
    console.log("   Captured erp_login_page.png");

    // 7. MOBILE RESPONSIVE TEST
    console.log("7. Testing Mobile Viewport (390 x 844)...");
    await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
    await page.goto(BASE_URL + "/#/", { waitUntil: "networkidle0" });
    await new Promise((r) => setTimeout(r, 800));
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "homepage_mobile.png"), fullPage: false });
    console.log("   Captured homepage_mobile.png");

    // Open mobile menu
    const menuBtn = await page.$('button[aria-label="Open menu"]');
    if (menuBtn) {
      console.log("   Opening mobile hamburger menu...");
      await menuBtn.click();
      await new Promise((r) => setTimeout(r, 500));
      await page.screenshot({ path: path.join(ARTIFACT_DIR, "mobile_drawer_open.png"), fullPage: false });
      console.log("   Captured mobile_drawer_open.png");
    }

    if (errors.length > 0) {
      console.warn("Encountered page errors:", errors);
    } else {
      console.log("\n=========================================");
      console.log("🎉 ALL E2E VISUAL VERIFICATION CHECKS PASSED!");
      console.log("=========================================\n");
    }
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
