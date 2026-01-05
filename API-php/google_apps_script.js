/**
 * Google Apps Script to fetch Business Activity Details from your PHP API.
 * 
 * INSTRUCTIONS:
 * 1. Open your Google Sheet (Workbook: "Filter", Sheet: "CODE").
 * 2. Go to Extensions > Apps Script.
 * 3. Delete any code in the editor and paste this entire script.
 * 4. Save the project (disk icon).
 * 5. Refresh your Google Sheet - you'll see a new menu "Activity Scraper"
 * 6. Click "Activity Scraper" > "Start Processing" to begin
 * 
 * The script will process rows in batches to avoid timeout issues.
 */

const CONFIG = {
    BASE_URL: "https://noaman.cloud",
    SCRIPT_PATH: "/api-php/scraper.php",
    SHEET_NAME: "CODE",
    START_ROW: 2,  // First data row (row 2, after header)
    CODE_COLUMN: 1,  // Column A
    STATUS_COLUMN: 2,  // Column B
    DATA_START_COLUMN: 3,  // Column C (where data starts)
    BATCH_SIZE: 5,  // Process 5 rows per batch
    MAX_EXECUTION_TIME: 240 // Stop after 4 minutes (240 seconds) to be safe
};

/**
 * Automatically runs when spreadsheet opens
 * Creates the menu (cannot auto-start due to Google security restrictions)
 */
function onOpen() {
    const ui = SpreadsheetApp.getUi();
    const menu = ui.createMenu('Activity Scraper');

    // Check if running
    const properties = PropertiesService.getScriptProperties();
    if (properties.getProperty('LAST_PROCESSED_ROW')) {
        menu.addItem('▶️ RESUME PROCESSING', 'continueProcessing');
        menu.addItem('🔄 RESET & START OVER', 'startProcessing');
    } else {
        menu.addItem('▶️ START PROCESSING', 'startProcessing');
    }

    menu.addToUi();

    // Show a small popup to remind user
    SpreadsheetApp.getActive().toast('Click "Activity Scraper" > "Start" to run.', 'Script Ready', 10);
}

/**
 * Start processing from the beginning (clears all data first)
 */
function startProcessing() {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
    if (!sheet) return;

    const lastRow = sheet.getLastRow();

    // Clear all previous data in columns B through G
    if (lastRow >= CONFIG.START_ROW) {
        const numRows = lastRow - CONFIG.START_ROW + 1;
        const numCols = 6;  // Columns B, C, D, E, F, G
        sheet.getRange(CONFIG.START_ROW, CONFIG.STATUS_COLUMN, numRows, numCols).clearContent();
        SpreadsheetApp.flush();
    }

    // Reset the progress tracker
    PropertiesService.getScriptProperties().deleteProperty('LAST_PROCESSED_ROW');
    PropertiesService.getScriptProperties().deleteProperty('START_TIME');
    PropertiesService.getScriptProperties().deleteProperty('TOTAL_PROCESSED');

    // Start processing
    continueProcessing();
}

/**
 * Continue processing from where it left off
 */
function continueProcessing() {
    const executionStartTime = new Date();
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);

    if (!sheet) {
        SpreadsheetApp.getUi().alert('Sheet "' + CONFIG.SHEET_NAME + '" not found!');
        return;
    }

    const properties = PropertiesService.getScriptProperties();
    const lastRow = sheet.getLastRow();

    // Get progress from last run
    let currentRow = parseInt(properties.getProperty('LAST_PROCESSED_ROW') || CONFIG.START_ROW);
    let totalProcessed = parseInt(properties.getProperty('TOTAL_PROCESSED') || '0');
    let globalStartTime = properties.getProperty('START_TIME');

    if (!globalStartTime) {
        globalStartTime = executionStartTime.getTime().toString();
        properties.setProperty('START_TIME', globalStartTime);
    }

    let totalErrors = 0;

    // Process rows until time runs out or we finish
    while (currentRow <= lastRow) {
        // Check execution time BEFORE processing the row
        // If we are already past 4 minutes, stop now to be safe
        const elapsed = (new Date() - executionStartTime) / 1000;
        if (elapsed > CONFIG.MAX_EXECUTION_TIME) {
            break;
        }

        const code = sheet.getRange(currentRow, CONFIG.CODE_COLUMN).getValue();

        // Skip if no code
        if (!code || code.toString().trim() === "") {
            currentRow++;
            continue;
        }

        // Update status to "Processing..."
        sheet.getRange(currentRow, CONFIG.STATUS_COLUMN).setValue("Processing...");
        SpreadsheetApp.flush();

        try {
            // Fetch data
            const data = fetchOne(code);

            // Check if error
            if (data[0] && (data[0].includes("Error:") || data[0].includes("Timeout:") || data[0].includes("Script Error:"))) {
                sheet.getRange(currentRow, CONFIG.STATUS_COLUMN).setValue("Error");
                // Write the actual error message to Column C (AR Name column) so user can see it
                sheet.getRange(currentRow, CONFIG.DATA_START_COLUMN).setValue(data[0]);
                totalErrors++;
            } else {
                // Write data to columns C, D, E, F, G
                sheet.getRange(currentRow, CONFIG.DATA_START_COLUMN, 1, 5).setValues([data]);

                // Mark as completed
                sheet.getRange(currentRow, CONFIG.STATUS_COLUMN).setValue("Completed");
                totalProcessed++;
            }
            SpreadsheetApp.flush();

            // Small delay
            Utilities.sleep(500);

        } catch (err) {
            sheet.getRange(currentRow, CONFIG.STATUS_COLUMN).setValue("Error: " + err.message);
            totalErrors++;
        }

        currentRow++;

        // Save progress after EVERY row to be safe
        properties.setProperty('LAST_PROCESSED_ROW', currentRow.toString());
        properties.setProperty('TOTAL_PROCESSED', totalProcessed.toString());
    }

    // Calculate timing
    const endTime = new Date();
    const executionElapsed = Math.round((endTime - executionStartTime) / 1000);

    // Check if we're done
    if (currentRow > lastRow) {
        // Calculate total time
        const totalElapsedMs = endTime.getTime() - parseInt(globalStartTime);
        const totalSeconds = Math.round(totalElapsedMs / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const totalFormatted = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;

        const avgSeconds = totalProcessed > 0 ? Math.round(totalElapsedMs / totalProcessed / 1000) : 0;

        // Clear progress
        properties.deleteProperty('LAST_PROCESSED_ROW');
        properties.deleteProperty('START_TIME');
        properties.deleteProperty('TOTAL_PROCESSED');

        // Delete any pending triggers
        deleteAllTriggers();

        SpreadsheetApp.getUi().alert(
            '✓ ALL PROCESSING COMPLETE!\n\n' +
            'Total Processed: ' + totalProcessed + '\n' +
            'Errors: ' + totalErrors + '\n\n' +
            'Total Time: ' + totalFormatted + '\n' +
            'Avg Time/Row: ' + avgSeconds + 's'
        );
    } else {
        // More rows to process - schedule next run automatically
        const remaining = lastRow - currentRow + 1;

        // Create a trigger to run the next execution in 10 seconds
        createNextBatchTrigger();

        Logger.log(
            'Time limit reached. Processed ' + totalProcessed + ' rows total. ' +
            'Detailed stats: ' + executionElapsed + 's execution. ' +
            'Remaining: ' + remaining + ' rows. Next run in 10 seconds...'
        );
    }
}

/**
 * Create a time-based trigger to run the next batch
 */
function createNextBatchTrigger() {
    // Delete existing triggers first
    deleteAllTriggers();

    // Create a trigger to run in 5 seconds
    ScriptApp.newTrigger('continueProcessing')
        .timeBased()
        .after(5000)  // 5 seconds
        .create();
}

/**
 * Delete all existing triggers
 */
function deleteAllTriggers() {
    const triggers = ScriptApp.getProjectTriggers();
    for (let i = 0; i < triggers.length; i++) {
        if (triggers[i].getHandlerFunction() === 'continueProcessing') {
            ScriptApp.deleteTrigger(triggers[i]);
        }
    }
}

/**
 * Fetches activity details and returns a row of data.
 *
 * @param {string} code The activity code (e.g. "013001")
 * @return {Array<string>} The details (AR Name, EN Name, Location, Eligible, Approvals).
 */
function fetchOne(code) {
    // Check cache first (6 hour cache to speed up repeated requests)
    const cache = CacheService.getScriptCache();
    const cacheKey = `activity_${code}`;
    const cached = cache.get(cacheKey);

    if (cached) {
        try {
            return JSON.parse(cached);
        } catch (e) {
            // Cache corrupted, continue to fetch
        }
    }

    // Construct URL
    const url = `${CONFIG.BASE_URL}${CONFIG.SCRIPT_PATH}?code=${encodeURIComponent(code)}`;

    try {
        // Options for URL Fetch
        const options = {
            'method': 'get',
            'muteHttpExceptions': true
        };

        const response = UrlFetchApp.fetch(url, options);
        const text = response.getContentText();
        const responseCode = response.getResponseCode();

        if (responseCode !== 200) {
            return [`Error: HTTP ${responseCode}`, text.substring(0, 100), "", "", ""];
        }

        // Parse JSON
        let json;
        try {
            json = JSON.parse(text);
        } catch (e) {
            // If JSON parsing fails, maybe PHP returned raw HTML error or mixed content
            const match = text.match(/\{[\s\S]*"status":[\s\S]*\}/);
            if (match) {
                try {
                    json = JSON.parse(match[0]);
                } catch (e2) {
                    return ["Error: Invalid JSON", text.substring(0, 100), "", "", ""];
                }
            } else {
                return ["Error: Invalid Output", text.substring(0, 100), "", "", ""];
            }
        }

        if (json.status === "error") {
            return [`API Error: ${json.message}`, "", "", "", ""];
        }

        if (json.status === "success" && json.data) {
            const d = json.data;

            // Google Sheets has a 50,000 character limit per cell
            const truncate = (str, maxLen = 45000) => {
                if (!str) return "N/A";
                if (str.length <= maxLen) return str;
                return str.substring(0, maxLen) + "... [TRUNCATED]";
            };

            // Order of columns: AR Name | EN Name | Locations | Eligible | Approvals
            const result = [
                truncate(d.name_ar, 1000),
                truncate(d.name_en, 1000),
                truncate(d.locations, 10000),
                truncate(d.eligible, 5000),
                truncate(d.approvals, 25000)
            ];

            // Cache the result for 6 hours (21600 seconds)
            try {
                cache.put(cacheKey, JSON.stringify(result), 21600);
            } catch (e) {
                // Cache failed, not critical
            }

            return result;
        }

        return ["Unknown Error", "", "", "", ""];

    } catch (err) {
        // Check if it's a timeout error
        if (err.message && err.message.includes("timeout")) {
            return ["Timeout: API took too long. Try again.", "", "", "", ""];
        }
        return [`Script Error: ${err.message}`, "", "", "", ""];
    }
}
