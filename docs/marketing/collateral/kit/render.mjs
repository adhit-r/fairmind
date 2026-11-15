// Render HTML collateral to PNG or PDF. Usage:
//   node render.mjs page.html out.png 1080 1350        (PNG at 2x)
//   node render.mjs page.html out.pdf A4               (PDF, print backgrounds)
import { chromium } from "/Users/adhi/axonome/fairmind/apps/frontend/node_modules/playwright/index.mjs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const [, , src, out, a, b] = process.argv;
const exe = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const browser = await chromium.launch({ executablePath: exe, args: ["--headless=new"] });
const page = await browser.newPage(out.endsWith(".png")
  ? { viewport: { width: +a, height: +b }, deviceScaleFactor: 2 } : {});
await page.goto(pathToFileURL(path.resolve(src)).href, { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
if (out.endsWith(".png")) await page.screenshot({ path: out, clip: { x: 0, y: 0, width: +a, height: +b } });
else await page.pdf({ path: out, format: a || "A4", printBackground: true, preferCSSPageSize: true });
await browser.close();
console.log("wrote", out);
