<?php
/**
 * PHP API Endpoint for Qatar Investor Scraper
 * This calls the Node.js scraper and returns JSON
 * Usage: api.php?code=351009
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// Get activity code from query parameter
$code = isset($_GET['code']) ? $_GET['code'] : '';

if (empty($code)) {
    echo json_encode([
        "status" => "error",
        "message" => "Missing 'code' parameter. Usage: api.php?code=351009"
    ]);
    exit;
}

// Sanitize input
$code = preg_replace('/[^0-9]/', '', $code);

if (empty($code)) {
    echo json_encode([
        "status" => "error",
        "message" => "Invalid code format. Code must be numeric."
    ]);
    exit;
}

// Execute Node.js scraper
$command = "node scraper.js " . escapeshellarg($code) . " 2>&1";
$output = shell_exec($command);

if ($output === null) {
    echo json_encode([
        "status" => "error",
        "message" => "Failed to execute scraper. Make sure Node.js is installed."
    ]);
    exit;
}

// Return the JSON output from Node.js
echo $output;
?>
