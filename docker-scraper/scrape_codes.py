# pyright: reportMissingImports=false
import os
import argparse
import time
import re
import warnings
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Suppress gspread deprecation warnings
warnings.filterwarnings('ignore', category=UserWarning, module='gspread')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVE_DIR = os.path.join(SCRIPT_DIR, "drive")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# XPath Constants
X_ACTIVITY_CODE_CONTAINER = "div.orange-text.ng-binding"
X_NEXT_BUTTON_LI = "//*[@id='pills-activities']//li[contains(@ng-click, 'nextPage()')]"
X_NEXT_BUTTON_LINK = "//*[@id='pills-activities']//li[contains(@ng-click, 'nextPage()')]//div[@class='page-link']"

def save_html_snapshot(driver, filename: str):
    """Save page HTML to output directory"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(OUTPUT_DIR, filename)
        content = driver.page_source
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

def get_page_indicator_text(driver) -> str:
    """Get the page indicator text (e.g. 'Page 1 / 280')"""
    try:
        element = driver.find_element(By.CSS_SELECTOR, "div.page-number")
        text = element.text
        return (text or "").strip()
    except Exception:
        return ""

def get_page_numbers(driver):
    """
    Parse 'Page X / Y' from the UI.
    Returns (current_page, last_page) or (None, None) if not found.
    """
    text = get_page_indicator_text(driver)
    if not text:
        return None, None
    # Expected format: "Page 280 / 280"
    try:
        parts = text.replace("Page", "").strip().split("/")
        cur = int(parts[0].strip())
        last = int(parts[1].strip())
        return cur, last
    except Exception:
        return None, None

def get_activity_codes(driver) -> list:
    """Extract activity codes from current page using SeleniumBase"""
    try:
        # Get all activity code elements
        elements = driver.find_elements(By.CSS_SELECTOR, "div.orange-text.ng-binding")
        
        codes = []
        for el in elements:
            text = el.text
            text = (text or "").strip()
            # Only include if it's purely digits
            if text and text.isdigit():
                codes.append(text)
        
        return codes
    except Exception:
        return []

def codes_fingerprint(codes: list) -> str:
    """Fingerprint to detect page content change (order-sensitive)"""
    return "|".join(codes[:10]) if codes else ""

def wait_for_codes_change(driver, previous_codes: list, timeout: int = 20) -> list:
    """Wait until the activity code list changes compared to previous page"""
    prev_fp = codes_fingerprint(previous_codes)
    start = time.time()
    
    while (time.time() - start) < timeout:
        codes = get_activity_codes(driver)
        if codes and codes_fingerprint(codes) != prev_fp:
            return codes
        time.sleep(0.5)
    
    return get_activity_codes(driver)

def is_next_button_disabled(driver) -> bool:
    """Check if the Next page button is disabled"""
    try:
        next_button = driver.find_element(By.XPATH, X_NEXT_BUTTON_LI)
        class_attr = next_button.get_attribute("class")
        return "disabled" in (class_attr or "")
    except Exception:
        return True

def get_total_results_count(driver, timeout: int = 5) -> int:
    """
    Read the total results count from the page (e.g. '2795')
    Returns the integer count or None if not found.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.result-search-info span"))
        )
        text = element.text
        text = (text or "").strip()
        
        if text:
            # Extract just digits (with optional commas)
            match = re.search(r'(\d[\d,]*)', text)
            if match:
                count_str = match.group(1).replace(',', '')
                return int(count_str)
    except Exception:
        pass
    return None

def get_expected_pages(driver, timeout: int = 5) -> int:
    """
    Read the expected total pages from the page (e.g. 'Page 1 / 280')
    Returns the integer page count or None if not found.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.page-number"))
        )
        text = element.text
        text = (text or "").strip()
        
        if text:
            # Extract total pages from "Page X / Y" format
            match = re.search(r'Page\s+\d+\s*/\s*(\d+)', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
            # Fallback: extract last number
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                return int(numbers[-1])
    except Exception:
        pass
    return None

def set_page_size_30(driver) -> bool:
    """
    Set the page size dropdown to 30 rows per page.
    """
    try:
        # Select 30 from the dropdown
        from selenium.webdriver.support.ui import Select
        dropdown_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "page_num_select"))
        )
        select = Select(dropdown_element)
        select.select_by_visible_text("30")
        
        # Wait for the page to reload
        time.sleep(3) # Give it a moment to trigger update
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.orange-text.ng-binding"))
        )
        
        return True
    except Exception as e:
        print(f"Warning: Could not set page size to 30: {e}")
        return False

def wait_for_results(driver, expected_count: int = 30, timeout: int = 15) -> int:
    """Wait until the expected number of activity codes are rendered"""
    start = time.time()
    
    while (time.time() - start) < timeout:
        actual_count = len(get_activity_codes(driver))
        
        if actual_count == expected_count:
            return actual_count
        
        # Check if we're on the last page (next button disabled)
        if is_next_button_disabled(driver) and actual_count > 0:
            return actual_count
        
        time.sleep(0.5)
    
    # Return whatever we have after timeout
    return len(get_activity_codes(driver))

def save_codes_bulk(worksheet, start_row: int, codes: list) -> bool:
    """
    Save a page of codes in bulk with retries.
    Returns True if saved, False otherwise.
    """
    if not worksheet or not codes:
        return True
    
    # Write codes as strings (Column A is already formatted as TEXT to preserve leading zeros)
    values = [[str(c)] for c in codes]
    end_row = start_row + len(codes) - 1
    range_notation = f"A{start_row}:A{end_row}"
    
    for _ in range(3):
        try:
            worksheet.update(range_notation, values)
            return True
        except Exception:
            time.sleep(1)
    
    # Fallback (slower) – ensures last page isn't lost
    try:
        for i, c in enumerate(codes):
            worksheet.update_cell(start_row + i, 1, str(c))
        return True
    except Exception:
        return False

def format_column_as_text(worksheet):
    """Format Column A as TEXT to preserve leading zeros"""
    try:
        worksheet.format("A:A", {
            "numberFormat": {
                "type": "TEXT"
            }
        })
        return True
    except Exception as e:
        print(f"Warning: Could not format column as TEXT: {e}")
        return False

def connect_to_sheets():
    """Connect to Google Sheets using service account credentials"""
    try:
        credentials_file = os.path.join(DRIVE_DIR, "google-credentials.json")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(credentials)
        
        # Open Sheet "Filter", Worksheet "CODE"
        spreadsheet = client.open("Filter")
        worksheet = spreadsheet.worksheet("CODE")
        
        return worksheet
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def print_page_table(page_number: int, codes: list):
    """Print a professional table showing page number and activity codes"""
    try:
        print(f"\nPage {page_number}")
        print(f"Found {len(codes)} activities")
        print("┌─────────────┐")
        for code in codes:
            print(f"│ {code:<11} │")
        print("└─────────────┘")
    except UnicodeEncodeError:
        # Fallback for Windows console that doesn't support Unicode box chars
        print(f"\nPage {page_number}")
        print(f"Found {len(codes)} activities")
        print("+-------------+")
        for code in codes:
            print(f"| {code:<11} |")
        print("+-------------+")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Scrape activity codes from investor portal (SeleniumBase)')
    group = parser.add_mutually_exclusive_group()
    # Default is headless (invisible) unless --visible is provided
    group.add_argument('--visible', action='store_true', help='Run browser in visible mode (default is headless)')
    # Backward-compatible flag (still supported)
    group.add_argument('--headless', action='store_true', help='Run browser in headless mode (invisible)')
    args = parser.parse_args()
    
    # Determine headless mode (default True if not --visible)
    # SeleniumBase Driver arg is "headless", NOT "run_headless"
    is_headless = not args.visible
    
    # Start timing
    start_time = time.time()
    
    print("Browser started (SeleniumBase UC)")
    
    # Launch Chromium browser with SeleniumBase UC
    # uc=True enables Undetected ChromeDriver
    driver = Driver(uc=True, headless=is_headless)
    
    try:
        # Open the base URL
        base_url = "https://investor.sw.gov.qa/wps/portal/investors/home/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zivfxNXA393Q38LXy9DQzMAj0cg4NcLY0MDMz1w_Wj9KNQlISGGRkEOjuZBjm6Wxj7OxpCFRjgAI4G-sGpefoF2dlpjo6KigAeufkI/dz/d5/L2dBISEvZ0FBIS9nQSEh/"
        driver.get(base_url)
        
        # Wait for page to be fully loaded (generic wait)
        time.sleep(5)
        
        # Scroll to the very bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        # Click footer link
        # /html/body/footer/section[1]/div/div/div[2]/ul/li[2]/a
        footer_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/footer/section[1]/div/div/div[2]/ul/li[2]/a"))
        )
        footer_link.click()
        
        # Wait for page to load
        time.sleep(5)
        
        # Locate input field and type 10, then press ENTER
        input_xpath = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[1]/div/div/input"
        input_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, input_xpath))
        )
        input_field.clear()
        input_field.send_keys("10")
        from selenium.webdriver.common.keys import Keys
        input_field.send_keys(Keys.ENTER)
        
        # Wait 3 seconds
        time.sleep(3)
        
        # Click Remove button
        remove_button_xpath = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[1]/div/div/div/div/span"
        remove_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, remove_button_xpath))
        )
        remove_button.click()
        
        # Scroll again to the end of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        # Scroll up to the container with activity codes
        try:
            container_xpath = "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[3]"
            container = driver.find_element(By.XPATH, container_xpath)
            driver.execute_script("arguments[0].scrollIntoView();", container)
            time.sleep(1)
        except:
            pass
        
        # Set page size to 30 rows per page
        set_page_size_30(driver)
        
        # Wait for results to render
        wait_for_results(driver, expected_count=30, timeout=15)
        
        # Extract activity codes from the page
        activity_codes = get_activity_codes(driver)
        
        # Capture the expected total results and pages count from page 1
        expected_total_results = get_total_results_count(driver, timeout=5)
        expected_total_pages = get_expected_pages(driver, timeout=5)
        
        print(f"\n{'='*40}")
        if expected_total_results:
            print(f"Expected Total Results: {expected_total_results}")
        else:
            print("Expected Total Results: Unknown")
        
        if expected_total_pages:
            print(f"Expected Total Pages:   {expected_total_pages}")
        else:
            print("Expected Total Pages:   Unknown")
        print(f"{'='*40}\n")
        
        # Connect to Google Sheets once at the beginning
        worksheet = connect_to_sheets()
        if not worksheet:
            print("Could not connect to Google Sheets, skipping save")
            worksheet = None
        else:
            # Set header in row 1
            worksheet.update_cell(1, 1, "Search")
            # Format Column A as TEXT to preserve leading zeros
            format_column_as_text(worksheet)
        
        # Save codes and handle pagination
        current_row = 2  # Start from row 2 (skip header in row 1)
        page_number = 1
        pages_processed = 0
        last_saved_fp = None
        
        while True:
            # Sync our displayed page number with the real UI page number
            ui_cur, ui_last = get_page_numbers(driver)
            if ui_cur:
                page_number = ui_cur
            
            # Display page table with activity codes
            if activity_codes:
                print_page_table(page_number, activity_codes)
            
            # Save current page codes in bulk
            if activity_codes and worksheet:
                try:
                    # Prevent saving the same page content twice
                    current_fp = codes_fingerprint(activity_codes)
                    if last_saved_fp == current_fp:
                        print("Skipped saving (duplicate page content)")
                    else:
                        saved_ok = save_codes_bulk(worksheet, current_row, activity_codes)
                        if saved_ok:
                            current_row += len(activity_codes)
                            print("Saved to sheet")
                            last_saved_fp = current_fp
                        else:
                            print("Error saving to sheet")
                except Exception as e:
                    print(f"Error saving to sheet: {e}")
            
            # Save page HTML snapshot for debugging
            save_html_snapshot(driver, f"output_page_{page_number}.html")
            pages_processed += 1
            
            # Check if Next button is disabled (dynamic stop condition)
            try:
                if is_next_button_disabled(driver):
                    print("\nReached last page (Next button disabled)")
                    break
            except Exception as e:
                print(f"\nCould not locate Next button: {e}")
                break
            
            # Try to click next page button
            try:
                before_text = get_page_indicator_text(driver)
                before_codes = activity_codes
                
                # Click next (find the clickable element inside the li)
                next_button_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, X_NEXT_BUTTON_LINK))
                )
                
                # Try regular click, fall back to JS click
                try:
                    next_button_link.click()
                except:
                    driver.execute_script("arguments[0].click();", next_button_link)
                
                # Wait for page indicator to change
                start_wait = time.time()
                while time.time() - start_wait < 15:
                    new_text = get_page_indicator_text(driver)
                    if new_text != before_text:
                        break
                    time.sleep(0.5)
                
                # After navigation, re-sync page number from UI
                ui_cur2, ui_last2 = get_page_numbers(driver)
                if ui_cur2:
                    page_number = ui_cur2
                
                # Wait for network stabilization
                time.sleep(2)
                
                # Wait for results to render
                wait_for_results(driver, expected_count=30, timeout=15)
                
                # Scroll to container
                try:
                    container = driver.find_element(By.XPATH, "/html/body/div[4]/div/div/section/div[2]/main/section[3]/div/div/div[3]")
                    driver.execute_script("arguments[0].scrollIntoView();", container)
                    time.sleep(1)
                except:
                    pass
                
                # Extract codes from new page
                activity_codes = wait_for_codes_change(driver, before_codes, timeout=25)
                
            except Exception as e:
                save_html_snapshot(driver, f"output_stopped_page_{page_number}.html")
                print(f"Stopped pagination at page {page_number}: {e}")
                break
        
        # Print summary
        total_activities_saved = current_row - 2
        
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print(f"\n{'='*40}")
        print(f"{'SUMMARY':^40}")
        print(f"{'='*40}")
        print(f"\nElapsed Time:    {minutes}m {seconds}s")
        
        # Determine actual pages processed
        final_cur, final_last = get_page_numbers(driver)
        actual_pages = final_last if final_last else pages_processed
        
        # Pages comparison
        print(f"\nPages:")
        if expected_total_pages is not None:
            print(f"  Expected:      {expected_total_pages}")
            print(f"  Actual:        {actual_pages}")
            if actual_pages == expected_total_pages:
                print(f"  Status:        ✓ OK")
            else:
                pages_diff = actual_pages - expected_total_pages
                if pages_diff > 0:
                    print(f"  Status:        ✗ MISMATCH (Excess: +{pages_diff})")
                else:
                    print(f"  Status:        ✗ MISMATCH (Missing: {pages_diff})")
        else:
            print(f"  Actual:        {actual_pages}")
            print(f"  Status:        Unknown (could not read expected pages)")
        
        # Results comparison
        print(f"\nResults:")
        if expected_total_results is not None:
            print(f"  Expected:      {expected_total_results}")
            print(f"  Scraped/Saved: {total_activities_saved}")
            
            # Validation status
            if total_activities_saved == expected_total_results:
                print(f"  Status:        ✓ OK")
            else:
                diff = total_activities_saved - expected_total_results
                if diff > 0:
                    print(f"  Status:        ✗ MISMATCH (Excess: +{diff})")
                else:
                    print(f"  Status:        ✗ MISMATCH (Missing: {diff})")
        else:
            print(f"  Scraped/Saved: {total_activities_saved}")
            print(f"  Status:        Unknown (could not read expected total)")
        
        print(f"\n{'='*40}")
        
        # Save the full page HTML source
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        content = driver.page_source
        with open(os.path.join(OUTPUT_DIR, "output.html"), "w", encoding="utf-8") as f:
            f.write(content)
        
        # Keep browser open for 5 seconds
        time.sleep(5)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        try:
            driver.save_screenshot("error.png")
            print("Screenshot saved as error.png")
        except:
            pass
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
