---
name: "web_scraping"
description: "Ethical web scraping and HTML parsing with proper rate limiting and error handling"
version: "1.0.0"
author: "Agent Zero Team"
tags: ["web", "scraping", "html", "parsing", "requests", "beautifulsoup", "selenium"]
---

# Web Scraping Skill

This skill provides comprehensive web scraping capabilities with emphasis on ethical practices, proper error handling, and respectful automation.

## Core Capabilities

- **Static HTML scraping** with requests and BeautifulSoup
- **Dynamic content scraping** with JavaScript rendering support
- **Rate limiting and politeness** to respect server resources
- **robots.txt compliance** checking
- **User agent management** for proper identification
- **Error handling** for timeouts, HTTP errors, and parsing issues
- **Link extraction** and crawling capabilities

## Prerequisites

### Basic Scraping
```bash
pip install requests beautifulsoup4 lxml
```

### JavaScript-Rendered Content
```bash
pip install selenium webdriver-manager
# Or use Playwright:
pip install playwright
playwright install
```

### Advanced Features
```bash
pip install urllib3 certifi aiohttp
```

## Ethical Scraping Principles

### 1. Respect robots.txt
Always check and respect the site's robots.txt file:

```python
import requests
from urllib.robotparser import RobotFileParser

def can_fetch(url, user_agent="*"):
    """Check if URL is allowed by robots.txt"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.read()

    return rp.can_fetch(user_agent, url)

# Usage
if can_fetch("https://example.com/page"):
    # Proceed with scraping
    pass
```

### 2. Use Appropriate Rate Limiting
Add delays between requests to avoid overwhelming servers:

```python
import time
import random

# Fixed delay
time.sleep(2)  # 2 seconds between requests

# Random delay (more human-like)
time.sleep(random.uniform(1, 3))  # 1-3 seconds
```

### 3. Identify Your Bot
Use descriptive User-Agent headers:

```python
headers = {
    "User-Agent": "MyBot/1.0 (contact@example.com; Educational scraper)"
}
response = requests.get(url, headers=headers)
```

### 4. Handle Errors Gracefully
Implement proper error handling and retries:

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """Create session with automatic retries"""
    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
```

## Basic Scraping Workflow

### Step 1: Fetch the Page

```python
import requests
from bs4 import BeautifulSoup

url = "https://example.com"
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; MyBot/1.0)"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Raise exception for bad status codes

    html_content = response.text

except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### Step 2: Parse the HTML

```python
soup = BeautifulSoup(html_content, 'lxml')

# Extract title
title = soup.find('h1')
if title:
    print(f"Title: {title.text.strip()}")

# Extract all paragraphs
paragraphs = soup.find_all('p')
for p in paragraphs:
    print(p.text.strip())

# Extract links
links = soup.find_all('a', href=True)
for link in links:
    print(f"Link: {link['href']}, Text: {link.text}")
```

### Step 3: Extract Structured Data

```python
# Using CSS selectors
articles = soup.select('article.post')
for article in articles:
    title = article.select_one('h2.title')
    author = article.select_one('span.author')
    date = article.select_one('time')

    print(f"Title: {title.text if title else 'N/A'}")
    print(f"Author: {author.text if author else 'N/A'}")
    print(f"Date: {date.text if date else 'N/A'}")
    print("---")
```

## Using Provided Scripts

### scrape_page.py - Basic Page Scraping

Extract content from a single page:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "web_scraping",
        "script_path": "scripts/scrape_page.py",
        "script_args": {
            "url": "https://example.com",
            "selector": "h1, p"
        }
    }
}
```

### extract_links.py - Link Extraction

Extract all links from a page:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "web_scraping",
        "script_path": "scripts/extract_links.py",
        "script_args": {
            "url": "https://example.com",
            "filter_domain": "example.com"
        }
    }
}
```

## Advanced Techniques

### JavaScript-Rendered Content

For sites that require JavaScript execution:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_with_selenium(url):
    """Scrape JavaScript-rendered content"""
    options = Options()
    options.add_argument('--headless')  # Run without GUI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        # Wait for specific element to load
        wait = WebDriverWait(driver, 10)
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".content"))
        )

        # Get page source after JavaScript execution
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        return soup

    finally:
        driver.quit()
```

### Handling Pagination

```python
def scrape_multiple_pages(base_url, max_pages=10):
    """Scrape content from multiple pages"""
    results = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Extract data from current page
            items = soup.find_all('div', class_='item')
            results.extend(items)

            # Check if next page exists
            next_button = soup.find('a', class_='next')
            if not next_button:
                break

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return results
```

### Form Submission

```python
def submit_form(url, form_data):
    """Submit form and scrape results"""
    session = requests.Session()

    # GET the form page to get CSRF token if needed
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'lxml')

    # Extract CSRF token if present
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    if csrf_token:
        form_data['csrf_token'] = csrf_token.get('value')

    # Submit form
    response = session.post(url, data=form_data)

    return BeautifulSoup(response.content, 'lxml')
```

## Common Selectors

See [docs/selectors.md](docs/selectors.md) for comprehensive selector guide.

### Quick Reference

**By Tag:**
```python
soup.find('h1')              # First h1
soup.find_all('p')           # All paragraphs
```

**By Class:**
```python
soup.find('div', class_='content')
soup.find_all('span', class_='author')
```

**By ID:**
```python
soup.find(id='main')
soup.find('div', id='header')
```

**CSS Selectors:**
```python
soup.select('div.content p')     # All p inside div.content
soup.select_one('h1#title')      # First h1 with id="title"
soup.select('a[href^="http"]')   # Links starting with http
```

**Attribute Selection:**
```python
soup.find_all('a', href=True)           # All links with href
soup.find_all('img', src=True)          # All images with src
soup.find('meta', attrs={'name': 'description'})
```

## Error Handling

### Common Issues and Solutions

**Timeout Errors:**
```python
try:
    response = requests.get(url, timeout=10)
except requests.exceptions.Timeout:
    print("Request timed out. Try increasing timeout or retry later.")
```

**HTTP Errors:**
```python
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Page not found")
    elif e.response.status_code == 403:
        print("Access forbidden - check robots.txt")
    elif e.response.status_code == 429:
        print("Rate limited - slow down requests")
```

**Parsing Errors:**
```python
try:
    element = soup.find('div', class_='content')
    text = element.text.strip()
except AttributeError:
    print("Element not found - selector may be incorrect")
except Exception as e:
    print(f"Parsing error: {e}")
```

**Encoding Issues:**
```python
# Let requests handle encoding
response = requests.get(url)
response.encoding = response.apparent_encoding
html = response.text

# Or specify encoding
response = requests.get(url)
html = response.content.decode('utf-8', errors='ignore')
```

## Best Practices

### Performance Optimization

1. **Session Reuse:** Reuse sessions for multiple requests
2. **Connection Pooling:** Use session for automatic connection pooling
3. **Compression:** Enable gzip compression in headers
4. **Async Requests:** Use aiohttp for concurrent scraping
5. **Caching:** Cache responses to avoid redundant requests

### Data Storage

```python
import json
import csv

# Save as JSON
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Save as CSV
with open('data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'url', 'date'])
    writer.writeheader()
    writer.writerows(data)
```

### Monitoring and Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)

logger = logging.getLogger(__name__)

logger.info(f"Scraping {url}")
logger.error(f"Failed to scrape {url}: {error}")
```

## Legal and Ethical Considerations

⚠️ **Important:** Always ensure your scraping activities comply with:

1. **Terms of Service:** Check website's ToS before scraping
2. **Copyright Laws:** Respect copyright and intellectual property
3. **Privacy Laws:** Handle personal data according to GDPR/CCPA
4. **Rate Limits:** Don't overload servers with requests
5. **Commercial Use:** Be aware of restrictions on commercial use

### When NOT to Scrape

- Site explicitly prohibits scraping in ToS or robots.txt
- Data is available via official API
- Site has CAPTCHA or anti-bot measures
- Content is behind authentication/paywall
- Scraping would harm the site's performance

## Troubleshooting

See [docs/best_practices.md](docs/best_practices.md) for detailed troubleshooting guide.

### Quick Fixes

**Problem: Getting blocked by anti-bot measures**
- Use realistic User-Agent headers
- Add random delays between requests
- Rotate user agents
- Use session cookies properly

**Problem: JavaScript content not loading**
- Use Selenium or Playwright
- Check browser developer tools for XHR requests
- Look for API endpoints that serve the data

**Problem: Parsing fails with dynamic content**
- Wait for elements to load with WebDriverWait
- Check if content loads via AJAX
- Inspect network tab for data endpoints

## References

- [docs/selectors.md](docs/selectors.md) - CSS and XPath selector guide
- [docs/best_practices.md](docs/best_practices.md) - Ethical scraping guidelines
- [scripts/scrape_page.py](scripts/scrape_page.py) - Basic page scraping script
- [scripts/extract_links.py](scripts/extract_links.py) - Link extraction script

## Additional Resources

- BeautifulSoup Documentation: https://www.crummy.com/software/BeautifulSoup/
- Requests Documentation: https://requests.readthedocs.io/
- Selenium Documentation: https://selenium-python.readthedocs.io/
- robots.txt Specification: https://www.robotstxt.org/
