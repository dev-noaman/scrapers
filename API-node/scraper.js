#!/usr/bin/env node

const puppeteer = require('puppeteer');

// Configuration
const BASE_URL = "https://investor.sw.gov.qa/wps/portal/investors/home/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zivfxNXA393Q38LXy9DQzMAj0cg4NcLY0MDMz1w_Wj9KNQlISGGRkEOjuZBjm6Wxj7OxpCFRjgAI4G-sGJRfoF2dlpjo6KigD6q7KF/dz/d5/L0lHSkovd0RNQUZrQUVnQSEhLzROVkUvZW4!/";

// CSS Selectors (Puppeteer 24+ doesn't support XPath)
const SEL_LANG_TOGGLE = "#swChangeLangLink > div";
const CSS_RESULTS_FIRST_ACTIVITY_LINK = "#pills-activities a.ba-link";

async function getLang(page) {
    try {
        return await page.evaluate(() => document.documentElement.lang || "");
    } catch {
        return "";
    }
}

async function setLanguage(page, targetLang, timeoutS = 10) {
    try {
        const currentLang = await getLang(page);
        if (currentLang === targetLang) return true;

        await page.waitForSelector(SEL_LANG_TOGGLE, { visible: true, timeout: 10000 });
        await page.click(SEL_LANG_TOGGLE);

        const deadline = Date.now() + (timeoutS * 1000);
        while (Date.now() < deadline) {
            if (await getLang(page) === targetLang) {
                await page.waitForNetworkIdle({ timeout: 10000 }).catch(() => { });
                return true;
            }
            await new Promise(r => setTimeout(r, 250));
        }
        return false;
    } catch {
        return false;
    }
}

async function getTextBySelector(page, selector, timeout = 10000) {
    try {
        await page.waitForSelector(selector, { visible: true, timeout });
        const text = await page.$eval(selector, el => el.textContent);
        return (text || "").trim();
    } catch {
        return "";
    }
}

async function directToDetails(page, code) {
    const detailsUrl = `https://investor.sw.gov.qa/wps/portal/investors/information-center/ba/details?bacode=${code}`;
    await page.goto(detailsUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForNetworkIdle({ timeout: 30000 }).catch(() => { });

    // Wait for activity code to appear
    await page.waitForFunction(() => {
        const divs = document.querySelectorAll('div');
        for (const div of divs) {
            if (div.textContent.includes('Activity Code') || div.textContent.includes('رمز النشاط')) {
                return true;
            }
        }
        return false;
    }, { timeout: 30000 });

    return page;
}

async function additionalStepFooterSearch(page, code) {
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await page.waitForNetworkIdle({ timeout: 30000 }).catch(() => { });

    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)).catch(() => { });

    // Click Business Activities link in footer
    await page.waitForSelector('footer a', { visible: true, timeout: 20000 });
    await page.evaluate(() => {
        const links = Array.from(document.querySelectorAll('footer a'));
        const baLink = links.find(a => a.textContent.includes('Business') || a.textContent.includes('الأنشطة'));
        if (baLink) baLink.click();
    });

    await page.waitForNetworkIdle({ timeout: 30000 }).catch(() => { });

    // Search
    await page.waitForSelector('input[type="text"]', { visible: true, timeout: 20000 });
    await page.type('input[type="text"]', code);
    await page.keyboard.press('Enter');

    await page.waitForNetworkIdle({ timeout: 20000 }).catch(() => { });
    await page.waitForSelector('#pills-activities', { timeout: 20000 });

    // Find exact match
    const links = await page.$$(CSS_RESULTS_FIRST_ACTIVITY_LINK);
    let matchingLink = null;

    for (const link of links) {
        const href = await page.evaluate(el => el.getAttribute('href'), link);
        const match = href?.match(/[?&]bacode=(\d+)/);
        if (match && match[1] === code) {
            matchingLink = link;
            break;
        }
    }

    if (!matchingLink) {
        throw new Error(`No exact match found for code ${code}`);
    }

    // Click and handle popup
    const [popup] = await Promise.all([
        new Promise(resolve => {
            page.once('popup', resolve);
            setTimeout(() => resolve(null), 5000);
        }),
        matchingLink.click()
    ]);

    const detailsPage = popup || page;
    await detailsPage.waitForNetworkIdle({ timeout: 30000 }).catch(() => { });

    // Wait for content
    await detailsPage.waitForFunction(() => {
        return document.body.textContent.includes('Activity Code') || document.body.textContent.includes('رمز النشاط');
    }, { timeout: 30000 });

    return detailsPage;
}

async function getTableData(page) {
    try {
        // Find the locations table
        const data = await page.evaluate(() => {
            const tables = Array.from(document.querySelectorAll('table'));
            for (const table of tables) {
                const tbody = table.querySelector('tbody');
                if (!tbody) continue;

                const rows = Array.from(tbody.querySelectorAll('tr'));
                const result = [];

                for (const row of rows) {
                    const cells = Array.from(row.querySelectorAll('td'));
                    if (cells.length >= 3) {
                        result.push({
                            main: cells[0]?.textContent?.trim() || '',
                            sub: cells[1]?.textContent?.trim() || '',
                            fee: cells[2]?.textContent?.trim() || ''
                        });
                    }
                }

                if (result.length > 0) return result;
            }
            return [];
        });

        return data;
    } catch {
        return [];
    }
}

async function getEligibleStatus(page) {
    try {
        const items = await page.evaluate(() => {
            const uls = Array.from(document.querySelectorAll('ul'));
            for (const ul of uls) {
                const items = Array.from(ul.querySelectorAll('li')).map(li => li.textContent.trim()).filter(t => t);
                if (items.some(item => item.includes('Allowed') || item.includes('مسموح'))) {
                    return items;
                }
            }
            return [];
        });

        return items.length > 0 ? items.join('\n') : "No Business Requirements";
    } catch {
        return "No Business Requirements";
    }
}

async function getApprovalsData(page) {
    try {
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2)).catch(() => { });

        const approvals = [];
        for (let i = 0; i < 12; i++) {
            const btnSelector = `#heading${i} button`;
            const btn = await page.$(btnSelector);
            if (!btn) break;

            let title = await page.evaluate(el => el.textContent, btn).catch(() => `Approval ${i + 1}`);
            title = (title || "").trim();
            if (title && /^\d+\./.test(title)) {
                title = title.split('.', 2)[1].trim();
            }

            await btn.click().catch(() => { });

            let agency = "Not specified";
            const agencySelector = `#collapse${i} div div div:nth-of-type(1) div:nth-of-type(2)`;
            const agencyEl = await page.$(agencySelector);
            if (agencyEl) {
                agency = await page.evaluate(el => el.textContent, agencyEl).catch(() => "Not specified");
                agency = (agency || "Not specified").trim();
            }

            approvals.push({ num: i + 1, title, agency });
        }

        if (approvals.length === 0) return "No Approvals Needed";

        return approvals.map(a => `Approval ${a.num}: ${a.title}\nAgency ${a.num}: ${a.agency}`).join('\n\n');
    } catch {
        return "Error extracting approvals";
    }
}

async function scrapeActivityCode(code) {
    const browser = await puppeteer.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--no-first-run',
            '--no-zygote',
            '--single-process'
        ]
    });

    try {
        const page = await browser.newPage();
        await page.setDefaultTimeout(120000);

        // Optimization: Block unnecessary resources
        await page.setRequestInterception(true);
        page.on('request', (req) => {
            const resourceType = req.resourceType();
            if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
                req.abort();
            } else {
                req.continue();
            }
        });

        let detailsPage = page;
        let usedAdditional = false;

        // Try direct URL first
        try {
            await directToDetails(page, code);
        } catch (e) {
            // Fallback to footer search
            usedAdditional = true;
            detailsPage = await additionalStepFooterSearch(page, code);
        }

        // Extract data
        await setLanguage(detailsPage, "en");

        // Get activity code
        const activityCode = await detailsPage.evaluate(() => {
            const text = document.body.textContent;
            const match = text.match(/Activity Code[:\s]+(\d+)/i);
            return match ? match[1] : '';
        });

        if (!activityCode) {
            throw new Error("Activity code not found on details page");
        }

        const nameEn = await detailsPage.evaluate(() => {
            const allText = document.body.innerText;
            const lines = allText.split('\n').map(l => l.trim()).filter(l => l);

            // Find "Business Activity Name" line
            const labelIdx = lines.findIndex(l => l.includes('Business Activity Name'));
            if (labelIdx >= 0) {
                // The actual name should be the NEXT line
                if (labelIdx + 1 < lines.length) {
                    return lines[labelIdx + 1];
                }
            }

            // Fallback: finding text near Activity Code if label not found
            const codeIdx = lines.findIndex(l => l.includes('Activity Code'));
            if (codeIdx >= 0) {
                for (let i = codeIdx + 1; i < Math.min(codeIdx + 10, lines.length); i++) {
                    const candidate = lines[i];
                    if (candidate &&
                        candidate.length > 20 &&
                        !candidate.includes('Activity Code') &&
                        !candidate.includes('Business Activity Name')) {
                        return candidate;
                    }
                }
            }
            return '';
        });

        // Get Arabic name
        await setLanguage(detailsPage, "ar");
        const nameAr = await detailsPage.evaluate(() => {
            const allText = document.body.innerText;
            const lines = allText.split('\n').map(l => l.trim()).filter(l => l);

            // Arabic label for Business Activity Name is usually "اسم النشاط التجاري"
            const labelIdx = lines.findIndex(l => l.includes('اسم النشاط') || l.includes('Activity Name'));
            if (labelIdx >= 0 && labelIdx + 1 < lines.length) {
                return lines[labelIdx + 1];
            }

            // Fallback
            const codeIdx = lines.findIndex(l => l.includes('رمز النشاط'));
            if (codeIdx >= 0) {
                for (let i = codeIdx + 1; i < Math.min(codeIdx + 10, lines.length); i++) {
                    const candidate = lines[i];
                    if (candidate &&
                        candidate.length > 10 &&
                        /[\u0600-\u06FF]/.test(candidate)) {
                        return candidate;
                    }
                }
            }
            return '';
        });

        // Back to English
        await setLanguage(detailsPage, "en");

        // Locations
        const tableData = await getTableData(detailsPage);
        const locations = tableData.map((row, i) =>
            `Main Location ${i + 1}: ${row.main}\nSub Location ${i + 1}: ${row.sub}\nFee ${i + 1}: ${row.fee}`
        ).join('\n\n');

        // Eligible
        const eligible = await getEligibleStatus(detailsPage);

        // Approvals
        const approvals = await getApprovalsData(detailsPage);

        return {
            status: "success",
            data: {
                activity_code: activityCode,
                name_en: nameEn,
                name_ar: nameAr,
                locations: locations || "",
                eligible,
                approvals
            },
            error: null
        };

    } catch (error) {
        return {
            status: "error",
            data: null,
            error: error.message
        };
    } finally {
        await browser.close();
    }
}

// CLI or HTTP mode
if (require.main === module) {
    const code = process.argv[2];
    if (!code) {
        console.log(JSON.stringify({ status: "error", message: "Usage: node scraper.js <bacode>" }));
        process.exit(1);
    }

    scrapeActivityCode(code).then(result => {
        console.log(JSON.stringify(result, null, 2));
    }).catch(err => {
        console.log(JSON.stringify({ status: "error", message: err.message }));
        process.exit(1);
    });
}

module.exports = { scrapeActivityCode };
