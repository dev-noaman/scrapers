# User Guide: Auto-Processing Script

This script automatically processes all activity codes in your sheet, one row at a time, with status tracking.

## Setup

1. Open your Google Sheet (Workbook: **Filter**, Sheet: **CODE**)
2. Go to **Extensions > Apps Script**
3. Delete any existing code
4. Copy the entire content of [`google_apps_script.js`](file:///d:/Copy/Single_window_Adel/API-php/google_apps_script.js)
5. Paste it into the Apps Script editor
6. Click **Save** (💾 icon)
7. **Close the Apps Script tab** and return to your Google Sheet
8. **Refresh the page** (F5 or Ctrl+R)

## Usage

After refreshing, you'll see a new menu called **"Activity Scraper"** in the menu bar.

### Process All Rows

1. Click **Activity Scraper > Process All Rows**
2. The script will:
   - Start from row 2 (first data row)
   - For each row with a code in column A:
     - Update column B to "Processing..."
     - Fetch the data from the API
     - Fill columns C, D, E, F, G with the results
     - Update column B to "Completed"
   - Skip rows that are already "Completed"
   - Skip empty rows
3. A summary dialog will appear when done

### Clear Cache

Click **Activity Scraper > Clear Cache** to remove all cached results (useful if you need to re-fetch data).

## Column Layout

- **Column A**: Search (activity codes)
- **Column B**: Status (automatically updated: "Processing...", "Completed", "Error")
- **Column C**: AR-Activity (Arabic name)
- **Column D**: EN-Activity (English name)
- **Column E**: Location
- **Column F**: Eligible
- **Column G**: Approvals

## Features

- **Sequential Processing**: Processes one row at a time to avoid timeouts
- **Status Tracking**: Column B shows the current status of each row
- **Resume Support**: If interrupted, run again and it will skip completed rows
- **Caching**: Results are cached for 6 hours for faster re-processing
- **Error Handling**: Rows with errors are marked as "Error" in column B

## Tips

- The script processes about 1 row every 10-15 seconds
- For 30 rows, expect about 5-8 minutes total
- You can close the sheet and come back - progress is saved
- Already completed rows won't be re-processed
