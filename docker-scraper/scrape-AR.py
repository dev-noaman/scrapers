# pyright: reportMissingImports=false
import os
import argparse
import time
import warnings
import gspread
from typing import Optional, List, Tuple
from oauth2client.service_account import ServiceAccountCredentials
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Suppress gspread deprecation warnings
warnings.filterwarnings('ignore', category=UserWarning, module='gspread')

# ----------------------------
# Configuration
# ----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_DIR = os.path.join(SCRIPT_DIR, "drive")
GOOGLE_CREDENTIALS_FILE = os.path.join(DRIVE_DIR, "google-credentials.json")
SPREADSHEET_NAME = "Filter"
WORKSHEET_NAME = "AR"
BASE_URL = "https://investor.sw.gov.qa/wps/portal/investors/home/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zivfxNXA393Q38LXy9DQzMAj0cg4NcLY0MDMz1w_Wj9KNQlISGGRkEOjuZBjm6Wxj7OxpCFRjgAI4G-sGpefoF2dlpjo6KigAeufkI/dz/d5/L0lHSkovd0RNQUZrQUVnQSEhLzROVkUvYXI!/"

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


def format_column_b_as_text(worksheet):
    """Format Column B as TEXT to preserve leading zeros"""
    try:
        worksheet.format("B:B", {
            "numberFormat": {
                "type": "TEXT"
            }
        })
        return True
    except Exception as e:
        print(f"Warning: Could not format column B as TEXT: {e}")
        return False


def connect_to_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(credentials)
    return client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


def _safe_screenshot(driver, filename: str) -> None:
    try:
        driver.save_screenshot(filename)
    except Exception:
        pass


def _get_lang(driver) -> str:
    try:
        return driver.execute_script("return document.documentElement.lang") or ""
    except Exception:
        return ""


def set_language(driver, target_lang: str, timeout_s: int = 10) -> bool:
    """
    Toggle website language between Arabic and English.
    target_lang: 'ar' or 'en'
    """
    try:
        current_lang = _get_lang(driver)
        if current_lang == target_lang:
            return True

        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, X_LANG_TOGGLE))
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView();", btn)
        except Exception:
            pass
        btn.click()

        # Wait until language changes
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if _get_lang(driver) == target_lang:
                time.sleep(1) # Wait for reload
                return True
            time.sleep(0.5)
        return False
    except Exception:
        return False


def click_xpath(driver, xpath: str, timeout_ms: int = 10_000) -> None:
    element = WebDriverWait(driver, timeout_ms/1000).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )
    try:
        driver.execute_script("arguments[0].scrollIntoView();", element)
    except Exception:
        pass
    element.click()


def fill_css(driver, selector: str, value: str, timeout_ms: int = 10_000) -> None:
    element = WebDriverWait(driver, timeout_ms/1000).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
    )
    element.clear()
    element.send_keys(value)


def direct_to_details(driver, code: str) -> bool:
    """
    FASTEST APPROACH: Go directly to the details page using the bacode URL parameter.
    """
    # Construct direct URL to details page
    details_url = f"https://investor.sw.gov.qa/wps/portal/investors/information-center/ba/details?bacode={code}"
    
    driver.get(details_url)
    
    # Wait for the activity code element to be visible
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, X_ACTIVITY_CODE))
        )
        return True
    except TimeoutException:
        raise Exception("Details page did not load correctly via direct URL")


def additional_step_footer_business_search(driver, code: str):
    """
    Additional Step: use the footer Business Activities Search page to find and open the activity details.
    """
    driver.get(BASE_URL)
    
    # Scroll to footer and click Business activities
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    
    footer = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, X_FOOTER_BUSINESS_ACTIVITIES))
    )
    footer.click()
    
    # Type code and trigger search
    inp = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, X_FOOTER_SEARCH_INPUT))
    )
    inp.send_keys(code)
    try:
        inp.send_keys(Keys.ENTER)
    except Exception:
        pass
        
    # Prefer real SEARCH button if present; fall back to container click
    try:
        btn = driver.find_elements(By.XPATH, "//button[contains(translate(normalize-space(.), 'search', 'SEARCH'), 'SEARCH')]")
        if len(btn) > 0:
            btn[0].click()
        else:
            driver.find_element(By.XPATH, X_FOOTER_SEARCH_CONTAINER).click()
    except Exception:
        try:
            driver.find_element(By.XPATH, X_FOOTER_SEARCH_CONTAINER).click()
        except Exception:
            pass
            
    # Results render under pills-activities
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#pills-activities"))
    )
     
    # Click first link
    link = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, CSS_RESULTS_FIRST_ACTIVITY_LINK))
    )
    
    # Handle new tab logic if needed (Selenium stays on same window unless switched)
    # But usually simple clicks open in same window or we switch handles
    current_handles = driver.window_handles
    link.click()
    time.sleep(2)
    new_handles = driver.window_handles
    
    if len(new_handles) > len(current_handles):
        # Switch to new tab
        new_tab = [h for h in new_handles if h not in current_handles][0]
        driver.switch_to.window(new_tab)
        
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.XPATH, X_ACTIVITY_CODE))
    )


def get_text_xpath(driver, xpath: str, timeout_ms: int = 10_000) -> str:
    try:
        el = WebDriverWait(driver, timeout_ms/1000).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView();", el)
        except Exception:
            pass
        return (el.text or "").strip()
    except Exception:
        return ""


def get_table_data(driver) -> List[Tuple[str, str, str]]:
    try:
        tbody = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, X_TBODY))
        )
        try:
            driver.execute_script("arguments[0].scrollIntoView();", tbody)
        except Exception:
            pass
            
        rows = tbody.find_elements(By.TAG_NAME, "tr")
        n = len(rows)
        out: List[Tuple[str, str, str]] = []
        for i in range(1, n + 1):
            td1 = get_text_xpath(driver, f"{X_TBODY}/tr[{i}]/td[1]")
            td2 = get_text_xpath(driver, f"{X_TBODY}/tr[{i}]/td[2]")
            td3 = get_text_xpath(driver, f"{X_TBODY}/tr[{i}]/td[3]")
            if td1 or td2 or td3:
                out.append((td1, td2, td3))
        return out
    except Exception:
        return []


def get_eligible_status(driver) -> str:
    try:
        ul_xpath = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div/div/div[9]/div[2]/table/tbody/tr[2]/td/ul"
        try:
            ul_locator = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, ul_xpath))
            )
        except Exception:
            return "لا يوجد تفاصيل"
            
        items = ul_locator.find_elements(By.TAG_NAME, "li")
        texts = [item.text.strip() for item in items if item.text.strip()]
        
        if texts:
            return "\n".join(texts)
            
        return "لا يوجد تفاصيل"
    except Exception:
        return "لا يوجد تفاصيل"


def get_approvals_data(driver) -> str:
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
        time.sleep(0.5)
        
        heading = driver.find_elements(By.XPATH, "//h4[contains(text(), 'الموافقات المطلوبة')]")
        if len(heading) == 0:
            try:
                no_el = driver.find_elements(By.XPATH, X_NO_APPROVAL)
                if len(no_el) > 0:
                    txt = no_el[0].text.strip()
                    if txt and not any(str(i) in txt[:10] for i in range(1, 7)):
                        return "هذا النشاط لا يتطلب موافقة"
            except Exception:
                pass
                
        approval_data = []
        for i in range(12):
            btn_xpath = f"//*[@id='heading{i}']/button"
            btn = driver.find_elements(By.XPATH, btn_xpath)
            if len(btn) == 0:
                break
            
            try:
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", btn[0])
                except:
                    pass
                title_text = btn[0].text.strip()
                if title_text and title_text[0].isdigit() and "." in title_text[:5]:
                    title_text = title_text.split(".", 1)[1].strip()
                approval_title = title_text or f"الموافقة {i+1}"
            except Exception:
                approval_title = f"الموافقة {i+1}"
                
            # Click to expand
            try:
                btn[0].click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn[0])
            
            time.sleep(0.5)
            
            agency = "غير محدد"
            try:
                agency_el = driver.find_elements(By.XPATH, f"//*[@id='collapse{i}']/div/div/div[1]/div[2]")
                if len(agency_el) > 0:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView();", agency_el[0])
                    except:
                        pass
                    agency_txt = agency_el[0].text.strip()
                    agency = agency_txt or agency
            except Exception:
                pass
                
            approval_data.append((i + 1, approval_title, agency))
            
        if not approval_data:
            return "هذا النشاط لا يتطلب موافقة"
            
        parts = []
        for num, title, agency in approval_data:
            parts.append(f"الموافقة {num}: {title}\nالجهة {num}: {agency}")
        return "\n\n".join(parts)
    except Exception:
        return "Error extracting approvals"


def save_activity_code_to_sheet(worksheet, row_number: int, activity_code: str) -> bool:
    try:
        worksheet.update_cell(row_number, 2, str(activity_code))
        return True
    except Exception:
        return False


def save_to_sheet(worksheet, row_number: int, col: int, value: str) -> bool:
    try:
        worksheet.update_cell(row_number, col, value)
        return True
    except Exception:
        return False


def process_activity_code(driver, code: str, row_number: int, worksheet) -> bool:
    """
    Process a single activity code and write results to the sheet.
    """
    try:
        print(f"Processing row {row_number} with code {code} ...")
        
        # FASTEST APPROACH: Try direct URL first
        try:
            direct_to_details(driver, code)
            print("  ✓ Success")
        except Exception as e:
            print(f"\n  Direct URL failed: {e}")
            print(f"  Falling back to search methods...")
            
            # Fallback to search flow
            try:
                click_xpath(driver, X_SEARCH_ICON)
                click_xpath(driver, X_BUSINESS_TAB)
                fill_css(driver, CSS_SEARCH_INPUT, code)
                time.sleep(2)
                
                try:
                    click_xpath(driver, X_FIRST_ACTIVITY)
                    WebDriverWait(driver, 20).until(
                         EC.visibility_of_element_located((By.XPATH, X_ACTIVITY_CODE))
                    )
                except TimeoutException:
                     print("Additional Step: Footer Business Activities Search")
                     additional_step_footer_business_search(driver, code)
            except Exception as fallback_error:
                print(f"All methods failed: {fallback_error}")
                return False

        # Ensure Arabic mode first
        set_language(driver, "ar")
        
        # Extract activity code
        activity_code = get_text_xpath(driver, X_ACTIVITY_CODE)
        if not activity_code:
            return False
        save_activity_code_to_sheet(worksheet, row_number, activity_code)
        
        # Arabic activity name (Column C)
        set_language(driver, "ar")
        ar_name = get_text_xpath(driver, X_ACTIVITY_NAME)
        save_to_sheet(worksheet, row_number, 3, ar_name)
        
        # English activity name (Column D)
        if set_language(driver, "en"):
            en_name = get_text_xpath(driver, X_ACTIVITY_NAME)
            save_to_sheet(worksheet, row_number, 4, en_name)
            
        # Back to Arabic for the rest
        set_language(driver, "ar")
        
        # Location data (Column E)
        rows = get_table_data(driver)
        if rows:
            formatted = []
            for i, (main_location, sub_location, fee) in enumerate(rows, start=1):
                formatted.append(f"تصنيف الموقع {i}: {main_location}\nنوع الموقع {i}: {sub_location}\nالرسوم {i}: {fee}")
            save_to_sheet(worksheet, row_number, 5, "\n\n".join(formatted))
            
        # Eligible status (Column F)
        eligible = get_eligible_status(driver)
        save_to_sheet(worksheet, row_number, 6, eligible)
        
        # Approvals (Column G)
        approvals = get_approvals_data(driver)
        save_to_sheet(worksheet, row_number, 7, approvals)
        
        return True
    
    except Exception as e:
        print(f"Error processing activity code {code}: {e}")
        _safe_screenshot(driver, os.path.join(SCRIPT_DIR, f"error_row_{row_number}.png"))
        return False


def run(headless: bool) -> None:
    worksheet = connect_to_sheets()
    
    # Set headers
    worksheet.update_cell(1, 2, "Activity_Code")
    worksheet.update_cell(1, 3, "AR-Activity")
    worksheet.update_cell(1, 4, "EN-Activity")
    worksheet.update_cell(1, 5, "Location")
    worksheet.update_cell(1, 6, "Eligible")
    worksheet.update_cell(1, 7, "Approvals")
    
    # Format Column B as TEXT
    format_column_b_as_text(worksheet)
    
    codes = worksheet.col_values(1)[1:] # from row 2
    if not codes:
        print("No activity codes found in sheet")
        return
        
    start_time = time.time()
    total_success = 0
    total_failed = 0
    
    # Launch Browser with SeleniumBase UC
    driver = Driver(uc=True, headless=headless)
    
    try:
        for idx, code in enumerate(codes, start=2):
            ok = False
            try:
                driver.get(BASE_URL)
                time.sleep(3)
                ok = process_activity_code(driver, code, idx, worksheet)
            except Exception as e:
                print(f"Error: {e}")
                _safe_screenshot(driver, os.path.join(SCRIPT_DIR, f"error_row_{idx}.png"))
                
            if not ok:
                print(f"Failed to process {code}")
                total_failed += 1
            else:
                total_success += 1
                
    finally:
        driver.quit()
        
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("\n" + "="*70)
    print("SCRAPE SUMMARY (AR)")
    print("="*70)
    print(f"Elapsed Time:       {minutes}m {seconds}s")
    print(f"Total Success Rows: {total_success}")
    if total_failed > 0:
        print(f"Total Failed Rows:  {total_failed}")
    print("="*70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape AR details using SeleniumBase (default headless)")
    parser.add_argument("--visible", action="store_true", help="Run browser visible (default is headless)")
    args = parser.parse_args()
    
    run(headless=not args.visible)


if __name__ == "__main__":
    main()
