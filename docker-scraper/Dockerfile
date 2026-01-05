FROM seleniumbase/seleniumbase:latest

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire directory (scripts + drive folder)
COPY . .

# Default command: Run the Activity Codes scraper (user can override in docker-compose)
CMD ["python3", "scrape_codes.py"]
