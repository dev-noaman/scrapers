<?php
// scraper.php
// PHP Wrapper for Python Scraper
// Usage: php scraper.php {bacode}

header('Content-Type: application/json');

if ($argc < 2) {
    echo json_encode(["status" => "error", "message" => "Usage: php scraper.php <bacode>"]);
    exit(1);
}

$code = escapeshellarg($argv[1]);

// Command to run Python script
// Set PYTHONIOENCODING to utf-8 to avoid charmap errors on Windows
$command = "set PYTHONIOENCODING=utf-8 && python scraper.py --code $code --json"; // No --headless needed as it defaults to headless in main() logic

// Execute command
$output = shell_exec($command);

if ($output === null) {
    echo json_encode(["status" => "error", "message" => "Failed to execute Python script."]);
    exit(1);
}

// The Python script might output other logs to stderr (which shell_exec doesn't capture by default) or stdout.
// We expect the LAST line or the specific JSON block to be the result.
// But our Python script prints JSON via print() and other logs via print().
// In run_single, we muted other prints or ensuring JSON is distinct?
// Actually scrape-EN.py prints "Processing row..." etc.
// We need to make sure ONLY JSON is output or we parse the JSON from the output.

// Let's rely on finding the last JSON object in the output or assume run_single is clean.
// In run_single, I added prints: `print("Processing row...")` is inside `process_activity_code`.
// So stdout will be mixed.
// I should filter the output to find the JSON line.

// Regex to extract JSON block { "status": ... }
if (preg_match('/\{[\s\S]*"status":[\s\S]*\}/', $output, $matches)) {
    echo $matches[0];
} else {
    // If no JSON found, return raw output for debugging
    echo json_encode(["status" => "error", "message" => "No valid JSON output from scraper.", "raw_output" => $output]);
}
?>
