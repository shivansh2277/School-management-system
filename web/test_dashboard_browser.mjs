import puppeteer from "puppeteer-core";
import fs from "fs";
import path from "path";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://localhost:5173";

async function run() {
  console.log("Launching headless browser...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1280,900"],
    defaultViewport: { width: 1280, height: 900 },
  });

  try {
    const page = await browser.newPage();

    page.on("console", (msg) => console.log("PAGE LOG:", msg.text()));
    page.on("pageerror", (err) => console.log("PAGE ERROR:", err.message));

    console.log("Navigating to:", BASE_URL);
    await page.goto(BASE_URL, { waitUntil: "networkidle0" });

    // Check if on login page
    const passwordInput = await page.$('input[type="password"]');
    if (passwordInput) {
      console.log("Entering admin credentials...");
      await passwordInput.type("Admin@123");
      console.log("Submitting login form...");
      await Promise.all([
        page.waitForNavigation({ waitUntil: "networkidle0" }).catch(() => {}),
        page.click("form button"),
      ]);
      await new Promise((r) => setTimeout(r, 2500));
    }

    console.log("Verifying Dashboard loaded...");
    await page.waitForFunction(
      () => document.body.innerText.includes("Fees Overview"),
      { timeout: 15000 }
    );
    console.log("✓ Found 'Fees Overview' card");

    await page.waitForFunction(
      () => document.body.innerText.includes("Grievances & Feedback"),
      { timeout: 10000 }
    );
    console.log("✓ Found 'Grievances & Feedback' card");

    // Take screenshot of main dashboard
    await page.screenshot({ path: "../docs/browser_dashboard_upgraded.png" });
    console.log("✓ Saved ../docs/browser_dashboard_upgraded.png");

    // Click on Fees Remaining card to open defaulters modal
    console.log("Opening Pending Fee Students modal...");
    const clickedFeesRemaining = await page.evaluate(() => {
      const all = Array.from(document.querySelectorAll("*"));
      const match = all.find(
        (el) => el.children.length === 0 && el.textContent.trim() === "Fees Remaining"
      );
      if (match) {
        const box = match.closest(".cursor-pointer");
        if (box) {
          box.click();
          return true;
        }
      }
      return false;
    });

    if (!clickedFeesRemaining) {
      throw new Error("Could not find or click Fees Remaining card");
    }

    await page.waitForFunction(
      () => document.body.innerText.includes("Pending Fee Students"),
      { timeout: 10000 }
    );
    console.log("✓ Defaulters Modal opened");

    console.log("Waiting for pending fee table to load...");
    await page.waitForSelector("table thead th", { timeout: 15000 });

    // Verify requested columns are present in table header
    const headers = await page.$$eval("table thead th", (ths) =>
      ths.map((t) => t.innerText.trim())
    );
    console.log("Table headers:", headers);

    const requiredHeaders = [
      "Student Name",
      "Admission ID",
      "Class & Section",
      "Class Teacher",
      "Academic Year",
      "Fee Type",
      "Due Date",
      "Payment Status",
      "Pending Amount",
    ];
    for (const rh of requiredHeaders) {
      if (!headers.some((h) => h.toLowerCase().includes(rh.toLowerCase()))) {
        throw new Error(`Missing required header: ${rh}`);
      }
    }
    console.log("✓ All requested column headers verified in roster table");

    // Verify Total Pending Amount at the bottom
    const footerText = await page.evaluate(() => {
      const tfoot = document.querySelector("tfoot");
      return tfoot ? (tfoot.innerText || tfoot.textContent) : null;
    });
    console.log("Footer text detected:", footerText);
    if (!footerText || !footerText.toLowerCase().includes("total pending amount")) {
      throw new Error(`Missing 'Total Pending Amount' in table footer summary. Found: ${footerText}`);
    }
    console.log("✓ Verified 'Total Pending Amount:' summary in table footer");

    // Verify Export Report (CSV) button exists
    const hasExportBtn = await page.evaluate(() => {
      return Array.from(document.querySelectorAll("button")).some((b) =>
        b.textContent.includes("Export Report (CSV)")
      );
    });
    if (!hasExportBtn) {
      throw new Error("Missing 'Export Report (CSV)' button");
    }
    console.log("✓ Verified 'Export Report (CSV)' button");

    await page.screenshot({ path: "../docs/browser_dashboard_defaulters.png" });
    console.log("✓ Saved ../docs/browser_dashboard_defaulters.png");

    // Close modal
    await page.evaluate(() => {
      const closeBtn = Array.from(document.querySelectorAll("button")).find(
        (b) => b.textContent.trim() === "Close"
      );
      if (closeBtn) closeBtn.click();
    });
    await new Promise((r) => setTimeout(r, 600));

    // Click on the first grievance item in Grievances card
    console.log("Opening Grievance Details modal...");
    const clickedGrievance = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll("div.cursor-pointer"));
      const grievanceItem = cards.find((c) => c.innerText.includes("By "));
      if (grievanceItem) {
        grievanceItem.click();
        return true;
      }
      return false;
    });

    if (!clickedGrievance) {
      throw new Error("Could not find grievance item in dashboard feed");
    }

    await page.waitForFunction(
      () => document.body.innerText.includes("Conversation History"),
      { timeout: 10000 }
    );
    console.log("✓ Grievance Detail modal opened with Conversation History");

    // Verify Assign to Teacher dropdown exists
    const hasAssignSection = await page.evaluate(() => {
      return document.body.innerText.toLowerCase().includes("assign to teacher");
    });
    if (!hasAssignSection) {
      throw new Error("Missing 'Assign to Teacher' section");
    }
    console.log("✓ Found 'Assign to Teacher / Staff' section");

    // Type a reply
    const replyText = "Automated Browser Verification: Administrative office has reviewed this issue.";
    await page.type("textarea", replyText);

    // Click Send Reply
    await page.evaluate(() => {
      const sendBtn = Array.from(document.querySelectorAll("button")).find(
        (b) => b.textContent.trim() === "Send Reply"
      );
      if (sendBtn) sendBtn.click();
    });
    await new Promise((r) => setTimeout(r, 1500));
    console.log("✓ Sent admin reply");

    await page.screenshot({ path: "../docs/browser_dashboard_grievance.png" });
    console.log("✓ Saved ../docs/browser_dashboard_grievance.png");

    console.log("========================================");
    console.log("ALL BROWSER TESTS COMPLETED SUCCESSFULLY!");
    console.log("========================================");
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error("Browser test failed:", err);
  process.exit(1);
});
