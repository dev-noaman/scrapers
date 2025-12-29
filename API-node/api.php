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

// Execute Node.js scraper via HTTP
$url = "http://localhost:3000/?code=" . urlencode($code);

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 200);
$output = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($output === false) {
    echo json_encode([
        "status" => "error",
        "message" => "Failed to communicate with scraper service: $error"
    ]);
    exit;
}

if ($httpCode !== 200) {
    echo json_encode([
        "status" => "error",
        "message" => "Scraper service returned HTTP $httpCode: $output"
    ]);
    exit;
}

// Return the JSON output from Node.js
echo $output;
?>
