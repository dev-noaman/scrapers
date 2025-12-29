# pyright: reportMissingImports=false
import asyncio
import argparse
import os
import re
import time
import json
from typing import Optional, List, Tuple, Dict, Any

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Page

# ----------------------------
# Configuration
# ----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://investor.sw.gov.qa/wps/portal/investors/home/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zivfxNXA393Q38LXy9DQzMAj0cg4NcLY0MDMz1w_Wj9KNQlISGGRkEOjuZBjm6Wxj7OxpCFRjgAI4G-sGJRfoF2dlpjo6KigD6q7KF/dz/d5/L0lHSkovd0RNQUZrQUVnQSEhLzROVkUvZW4!/"

# Details page XPaths
X_ACTIVITY_CODE = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[1]/div[2]"
X_ACTIVITY_NAME = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[3]/div[2]"
X_TBODY = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[8]/div[2]/table/tbody"
X_ELIGIBLE = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[9]/div[2]/table/tbody/tr[2]/td"
X_NO_APPROVAL = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[10]/div[2]"

# Search flow selectors
X_SEARCH_ICON = "//*[@id='searchIconId']"
X_BUSINESS_TAB = "//*[@id='nav-business-tab']"
CSS_SEARCH_INPUT = "input#searchInput"
X_FIRST_ACTIVITY = "//*[@id='businessList']/li/a/div"
X_LANG_TOGGLE = "//*[@id='swChangeLangLink']/div"

# Additional Step (Footer Business Activities Search)
X_FOOTER_BUSINESS_ACTIVITIES = "/html/body/footer/section[1]/div/div/div[2]/ul/li[2]/a"
X_FOOTER_SEARCH_INPUT = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[1]/div/div/input"
X_FOOTER_SEARCH_CONTAINER = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[1]/div"
CSS_RESULTS_FIRST_ACTIVITY_LINK = "#pills-activities a.ba-link"


async def _safe_screenshot(page: Page, filename: str) -> None:
    pass


async def _get_lang(page: Page) -> str:
    try:
        return (await page.evaluate("document.documentElement.lang")) or ""
    except Exception:
        return ""


async def set_language(page: Page, target_lang: str, timeout_s: int = 10) -> bool:
    """
    Toggle website language between Arabic and English.
    """
    try:
        current_lang = await _get_lang(page)
        if current_lang == target_lang:
            return True

        btn = page.locator(f"xpath={X_LANG_TOGGLE}")
        await btn.wait_for(state="visible", timeout=10_000)
        try:
            await btn.scroll_into_view_if_needed()
        except Exception:
            pass
        await btn.click()

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if await _get_lang(page) == target_lang:
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass
                return True
            await asyncio.sleep(0.25)
        return False
    except Exception:
        return False


async def click_xpath(page: Page, xpath: str, timeout_ms: int = 10_000) -> None:
    el = page.locator(f"xpath={xpath}")
    await el.wait_for(state="visible", timeout=timeout_ms)
    try:
        await el.scroll_into_view_if_needed()
    except Exception:
        pass
    await el.click()


async def fill_css(page: Page, selector: str, value: str, timeout_ms: int = 10_000) -> None:
    el = page.locator(selector)
    await el.wait_for(state="visible", timeout=timeout_ms)
    await el.fill(value)


async def direct_to_details(page: Page, code: str) -> Page:
    """
    Go directly to the details page using the bacode URL parameter.
    """
    details_url = f"https://investor.sw.gov.qa/wps/portal/investors/information-center/ba/details?bacode={code}"
    
    await page.goto(details_url, wait_until="domcontentloaded")
    
    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:
        pass
    
    await page.locator(f"xpath={X_ACTIVITY_CODE}").wait_for(state="visible", timeout=30_000)
    
    return page


async def additional_step_footer_business_search(page: Page, code: str) -> Page:
    """
    Additional Step: use the footer Business Activities Search page.
    """
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:
        pass

    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    except Exception:
        pass
    footer = page.locator(f"xpath={X_FOOTER_BUSINESS_ACTIVITIES}")
    await footer.wait_for(state="visible", timeout=20_000)
    await footer.click()

    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:
        pass

    inp = page.locator(f"xpath={X_FOOTER_SEARCH_INPUT}")
    await inp.wait_for(state="visible", timeout=20_000)
    await inp.fill(code)
    try:
        await inp.press("Enter")
    except Exception:
        pass

    try:
        btn = page.locator("xpath=//button[contains(translate(normalize-space(.), 'search', 'SEARCH'), 'SEARCH')]")
        if await btn.count() > 0:
            await btn.first.click()
        else:
            await page.locator(f"xpath={X_FOOTER_SEARCH_CONTAINER}").click()
    except Exception:
        try:
            await page.locator(f"xpath={X_FOOTER_SEARCH_CONTAINER}").click()
        except Exception:
            pass

    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        pass

    results_root = page.locator("css=#pills-activities")
    await results_root.wait_for(state="attached", timeout=20_000)

    all_links = page.locator(f"css={CSS_RESULTS_FIRST_ACTIVITY_LINK}")
    await all_links.first.wait_for(state="visible", timeout=20_000)
    
    link = None
    count = await all_links.count()
    
    for i in range(count):
        cur = all_links.nth(i)
        href = await cur.get_attribute("href")
        bacode_match = re.search(r"(?:\?|&)bacode=(\d+)", href or "")
        bacode = bacode_match.group(1) if bacode_match else None
        
        if bacode == code:
            link = cur
            break
    
    if link is None:
        raise Exception(f"No exact match found for code {code}. Found {count} results but none matched exactly.")

    popup_page: Page | None = None
    try:
        async with page.expect_popup(timeout=20_000) as popup_info:
            await link.click()
        popup_page = await popup_info.value
    except Exception:
        await link.click()

    details_page = popup_page or page
    try:
        await details_page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:
        pass
    await details_page.locator(f"xpath={X_ACTIVITY_CODE}").wait_for(state="visible", timeout=30_000)
    return details_page


async def get_text_xpath(page: Page, xpath: str, timeout_ms: int = 10_000) -> str:
    el = page.locator(f"xpath={xpath}")
    await el.wait_for(state="visible", timeout=timeout_ms)
    try:
        await el.scroll_into_view_if_needed()
    except Exception:
        pass
    txt = await el.text_content()
    return (txt or "").strip()


async def get_table_data(page: Page) -> List[Tuple[str, str, str]]:
    try:
        tbody = page.locator(f"xpath={X_TBODY}")
        await tbody.wait_for(state="visible", timeout=10_000)
        try:
            await tbody.scroll_into_view_if_needed()
        except Exception:
            pass

        rows = tbody.locator("tr")
        n = await rows.count()
        out: List[Tuple[str, str, str]] = []
        for i in range(1, n + 1):
            td1 = await get_text_xpath(page, f"{X_TBODY}/tr[{i}]/td[1]")
            td2 = await get_text_xpath(page, f"{X_TBODY}/tr[{i}]/td[2]")
            td3 = await get_text_xpath(page, f"{X_TBODY}/tr[{i}]/td[3]")
            if td1 or td2 or td3:
                out.append((td1, td2, td3))
        return out
    except Exception:
        return []


async def get_eligible_status(page: Page) -> str:
    try:
        ul_xpath = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[9]/div[2]/table/tbody/tr[2]/td/ul"
        ul_locator = page.locator(f"xpath={ul_xpath}")
        
        try:
            await ul_locator.wait_for(state="visible", timeout=3000)
        except Exception:
            return "No Business Requirements"

        items = await ul_locator.locator("li").all_inner_texts()
        cleaned_items = [item.strip() for item in items if item.strip()]
        
        if cleaned_items:
            return "\n".join(cleaned_items)
            
        return "No Business Requirements"

    except Exception:
        return "No Business Requirements"


async def get_approvals_data(page: Page) -> str:
    try:
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        except Exception:
            pass

        heading = page.locator("xpath=//h4[contains(text(), 'الموافقات المطلوبة')]")
        if await heading.count() == 0:
            try:
                no_el = page.locator(f"xpath={X_NO_APPROVAL}")
                if await no_el.count() > 0:
                    txt = ((await no_el.text_content()) or "").strip()
                    if txt and not any(str(i) in txt[:10] for i in range(1, 7)):
                        return "No Approvals Needed"
            except Exception:
                pass

        approval_data = []
        for i in range(12):
            btn = page.locator(f"xpath=//*[@id='heading{i}']/button")
            if await btn.count() == 0:
                break
            try:
                try:
                    await btn.scroll_into_view_if_needed()
                except Exception:
                    pass
                title_text = ((await btn.text_content()) or "").strip()
                if title_text and title_text[0].isdigit() and "." in title_text[:5]:
                    title_text = title_text.split(".", 1)[1].strip()
                approval_title = title_text or f"Approval {i+1}"
            except Exception:
                approval_title = f"Approval {i+1}"

            try:
                await btn.click()
            except Exception:
                try:
                    await page.evaluate("(el) => el.click()", await btn.element_handle())
                except Exception:
                    pass

            agency = "Not specified"
            try:
                agency_el = page.locator(f"xpath=//*[@id='collapse{i}']/div/div/div[1]/div[2]")
                if await agency_el.count() > 0:
                    try:
                        await agency_el.scroll_into_view_if_needed()
                    except Exception:
                        pass
                    agency_txt = ((await agency_el.text_content()) or "").strip()
                    agency = agency_txt or agency
            except Exception:
                pass

            approval_data.append((i + 1, approval_title, agency))

        if not approval_data:
            return "No Approvals Needed"

        parts = []
        for num, title, agency in approval_data:
            parts.append(f"Approval {num}: {title}\nAgency {num}: {agency}")
        return "\n\n".join(parts)
    except Exception:
        return "Error extracting approvals"


async def process_activity_code(page: Page, code: str) -> tuple[bool, bool, str | None, Dict[str, Any]]:
    """
    Process a single activity code and return data.
    Returns: (success, used_additional, error_msg, data_dict)
    """
    popup_details_page: Page | None = None
    used_additional = False
    error_msg = None
    data = {}
    
    try:
        # 1. Navigate
        try:
            page = await direct_to_details(page, code)
        except Exception as e:
            # Fallback
            try:
                await click_xpath(page, X_SEARCH_ICON)
                await click_xpath(page, X_BUSINESS_TAB)
                await fill_css(page, CSS_SEARCH_INPUT, code)
                
                # Check for ambiguity
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass

                use_additional = False
                try:
                    await asyncio.sleep(1)
                    business_list = page.locator("//*[@id='businessList']/li")
                    if await business_list.count() > 1:
                        use_additional = True
                except Exception:
                    pass
                
                if use_additional:
                    used_additional = True
                    details_page = await additional_step_footer_business_search(page, code)
                    if details_page is not page:
                        popup_details_page = details_page
                        page = details_page
                else:
                    try:
                        await click_xpath(page, X_FIRST_ACTIVITY)
                        await page.wait_for_load_state("networkidle", timeout=20_000)
                        await page.locator(f"xpath={X_ACTIVITY_CODE}").wait_for(state="visible", timeout=20_000)
                    except PlaywrightTimeoutError:
                        used_additional = True
                        details_page = await additional_step_footer_business_search(page, code)
                        if details_page is not page:
                            popup_details_page = details_page
                            page = details_page

            except Exception as fallback_error:
                return False, used_additional, f"All methods failed: {fallback_error}", {}

        # 2. Extract Data
        await set_language(page, "en")
        
        extracted_code = await get_text_xpath(page, X_ACTIVITY_CODE)
        if not extracted_code:
             return False, used_additional, "Activity code not found", {}
        data['activity_code'] = extracted_code

        # English Name
        await set_language(page, "en")
        data['name_en'] = await get_text_xpath(page, X_ACTIVITY_NAME)

        # Arabic Name
        if await set_language(page, "ar"):
             data['name_ar'] = await get_text_xpath(page, X_ACTIVITY_NAME)
        else:
             data['name_ar'] = "Error switching to Arabic"

        # Back to English
        await set_language(page, "en")

        # Location
        rows = await get_table_data(page)
        if rows:
            formatted = []
            for i, (main_loc, sub_loc, fee) in enumerate(rows, start=1):
                formatted.append(f"Main Location {i}: {main_loc}\nSub Location {i}: {sub_loc}\nFee {i}: {fee}")
            data['locations'] = "\n\n".join(formatted)
        else:
            data['locations'] = ""

        # Eligible
        data['eligible'] = await get_eligible_status(page)

        # Approvals
        data['approvals'] = await get_approvals_data(page)

        return True, used_additional, None, data

    except Exception as e:
        await _safe_screenshot(page, os.path.join(SCRIPT_DIR, f"error_{code}.png"))
        return False, used_additional, str(e), {}
    finally:
        if popup_details_page is not None:
            try:
                await popup_details_page.close()
            except Exception:
                pass


async def run_single(code: str, headless: bool, json_output: bool) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        
        # Optimization: Block unnecessary resources
        async def block_aggressively(route):
            if route.request.resource_type in ["image", "font", "stylesheet"]:
                await route.abort()
            else:
                await route.continue_()
        
        await context.route("**/*", block_aggressively)
        
        page = await context.new_page()
        page.set_default_timeout(120_000)
        
        try:
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            success, _, error, data = await process_activity_code(page, code)
            
            if json_output:
                result = {
                    "status": "success" if success else "error",
                    "data": data if success else None,
                    "error": error
                }
                print(json.dumps(result, ensure_ascii=True, indent=2))
            else:
                if success:
                    print(f"Successfully scraped code {code}")
                    for k, v in data.items():
                        print(f"{k}: {v}")
                else:
                    print(f"Failed to scrape code {code}: {error}")
                    
        finally:
            await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape EN/AR details (Single Run Only)")
    parser.add_argument("--visible", action="store_true", help="Run browser visible (default is headless)")
    parser.add_argument("--code", type=str, required=True, help="Scrape a single activity code")
    parser.add_argument("--json", action="store_true", help="Output result as JSON to stdout")
    args = parser.parse_args()

    asyncio.run(run_single(args.code, headless=not args.visible, json_output=args.json))


if __name__ == "__main__":
    main()
