import puppeteer from "puppeteer-core";

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://localhost:5173";

async function run() {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
  });
  const page = await browser.newPage();
  page.on("console", msg => console.log("PAGE:", msg.text()));
  page.on("pageerror", err => console.log("PAGE ERROR:", err.message));

  await page.goto(BASE_URL, { waitUntil: "networkidle0" });
  const pw = await page.$('input[type="password"]');
  if (pw) {
    await pw.type("Admin@123");
    await Promise.all([
      page.waitForNavigation({ waitUntil: "networkidle0" }).catch(() => {}),
      page.click("form button"),
    ]);
  }
  await new Promise(r => setTimeout(r, 1000));
  await page.goto(`${BASE_URL}/#/inventory`, { waitUntil: "networkidle0" });
  await new Promise(r => setTimeout(r, 2000));
  console.log("URL:", page.url());
  console.log("BODY TEXT:\n", await page.evaluate(() => document.body.innerText));
  await browser.close();
}

run().catch(console.error);
