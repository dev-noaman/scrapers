# PHP Scraper Setup Guide

## Overview
This solution provides a robust PHP interface to the Qatar Investor Portal scraper. It uses a **Hybrid Approach** where PHP invokes a specialized Python Playwright script to handle the complex session and JavaScript rendering required by the portal.

## 📂 File Structure

| File | Description |
|------|-------------|
| **`scraper.php`** | The main PHP wrapper. Call this script to get data. |
| **`scraper.py`** | The core scraping logic using Playwright (Single Run Mode). |
| **`requirements.txt`** | List of Python dependencies. |

---

## 🚀 Installation

1.  **Install Python Dependencies:**
    Ensure you have Python installed, then run:
    ```bash
    pip install -r requirements.txt
    python -m playwright install chromium
    ```

2.  **Verify Setup:**
    Run the PHP script with a test code:
    ```bash
    php scraper.php 013001
    ```

---

## 💻 Usage

Run the `scraper.php` script from the command line or invoke it via `shell_exec` in your application.

**Command:**
```bash
php scraper.php {bacode}
```

**Example:**
```bash
php scraper.php 351009
```

---

## 📦 Output Format

The script returns a JSON object containing the status and scraped data.

### Success Response
```json
{
  "status": "success",
  "data": {
    "activity_code": "351009",
    "name_en": "Other activities of Electric power generation...",
    "name_ar": "أنشطة أخرى لتوليد الطاقة الكهربائية...",
    "locations": "Main Location 1: Commercial...",
    "eligible": "Allowed for GCC\nAllowed for Foreigners...",
    "approvals": "No Approvals Needed"
  },
  "error": null
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Detailed error message..."
}
```

---

## ⚙️ Technical Details

-   **Optimization**: The script first attempts a **Direct URL** access (`details?bacode={code}`) for maximum speed.
-   **Fallback**: If the direct URL fails (due to session issues), it automatically falls back to the **Search Interaction** method to ensure reliability.
-   **Encoding**: Handles `UTF-8` encoding correctly for Arabic text support on Windows consoles.