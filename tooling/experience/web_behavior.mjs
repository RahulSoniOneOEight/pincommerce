import { chromium } from "playwright";
const base=process.env.STORYBOOK_URL || "http://127.0.0.1:6006";
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1280,height:900}});
await page.goto(base+"/iframe.html?id=governance-behaviorparity--default&viewMode=story",{waitUntil:"networkidle"});

await page.getByRole("button",{name:"In stock"}).click();
if ((await page.getByTestId("filter-output").textContent()) !== "In stock") throw new Error("filter parity failed");

await page.getByRole("button",{name:"Increase Reference Product"}).click();
if ((await page.getByTestId("quantity-output").textContent()) !== "2") throw new Error("quantity parity failed");

await page.getByRole("button",{name:"Catalog"}).click();
if ((await page.getByTestId("navigation-output").textContent()) !== "Catalog") throw new Error("navigation parity failed");

const input=page.getByLabel("Name");
await input.fill("buyer");
if ((await page.getByTestId("form-output").textContent()) !== "buyer") throw new Error("form parity failed");

console.log(JSON.stringify({status:"passed",actions:["select-filter","change-quantity","navigate","change-field"]}));
await browser.close();
