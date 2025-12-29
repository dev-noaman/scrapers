# Qatar Investor Portal Scraper - Node.js Version

## 🚀 For Hostinger Shared Hosting

This solution uses **Node.js + Puppeteer** instead of Python, making it compatible with Hostinger shared hosting.

---

## 📦 Installation on Hostinger

### 1. Enable Node.js
- Log into your Hostinger control panel
- Go to **Advanced** → **Node.js**
- Enable Node.js (version 16 or higher recommended)

### 2. Upload Files
Upload these files to your hosting:
- `scraper.js`
- `package.json`
- `api.php` (optional, for HTTP API)

### 3. Install Dependencies
Connect via SSH and run:
```bash
cd /path/to/your/API/folder
npm install
```

This will install Puppeteer and its dependencies.

---

## 💻 Usage

### Option 1: Command Line
```bash
node scraper.js 351009
```

### Option 2: PHP API Endpoint
Access via browser or HTTP request:
```
https://yourdomain.com/api.php?code=351009
```

### Option 3: From Your PHP Code
```php
<?php
$code = "351009";
$command = "node scraper.js " . escapeshellarg($code);
$result = shell_exec($command);
$data = json_decode($result, true);

if ($data['status'] === 'success') {
    echo "Activity: " . $data['data']['name_en'];
}
?>
```

---

## 📦 Response Format

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

---

## ⚙️ Hostinger-Specific Notes

1. **Memory Limit**: Puppeteer needs at least 512MB RAM. Most Hostinger plans support this.
2. **Execution Time**: Set PHP `max_execution_time` to at least 60 seconds.
3. **Node.js Version**: Use Node.js 16+ for best compatibility.
4. **Chromium**: Puppeteer will download Chromium automatically during `npm install`.

---

## 🐛 Troubleshooting

**"Failed to launch browser"**
- Add to `scraper.js`: `args: ['--no-sandbox', '--disable-setuid-sandbox']` (already included)

**"Command not found: node"**
- Make sure Node.js is enabled in Hostinger control panel
- Check the correct Node.js path (might be `/usr/bin/node` or similar)

**Timeout errors**
- Increase timeout values in `scraper.js`
- Check your hosting plan's resource limits
