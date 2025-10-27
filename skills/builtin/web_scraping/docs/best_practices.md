# Web Scraping Best Practices and Ethical Guidelines

Comprehensive guide to responsible and effective web scraping.

## Ethical Scraping Principles

### 1. Legal Compliance

**Check Terms of Service (ToS)**
- Always read the website's Terms of Service before scraping
- Many sites explicitly prohibit automated access
- Violating ToS may result in legal action

**Copyright and Intellectual Property**
- Respect copyright laws when collecting content
- Don't republish scraped content without permission
- Give proper attribution when required

**Privacy Laws (GDPR, CCPA)**
- Be careful with personal data
- Understand data protection regulations
- Implement proper data handling procedures
- Respect user privacy preferences

### 2. Respect robots.txt

**What is robots.txt?**
A file that tells crawlers which pages they can and cannot access.

**How to Check:**
```python
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

def is_allowed(url, user_agent="*"):
    """Check if scraping is allowed"""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)

    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        # If can't read robots.txt, proceed with caution
        return True
```

**Example robots.txt:**
```
User-agent: *
Disallow: /admin/
Disallow: /private/
Crawl-delay: 10

User-agent: Googlebot
Allow: /

Sitemap: https://example.com/sitemap.xml
```

**Best Practices:**
- Always check robots.txt before scraping
- Respect Disallow directives
- Honor Crawl-delay values
- Don't bypass robots.txt programmatically

### 3. Rate Limiting

**Why Rate Limit?**
- Avoid overwhelming servers
- Prevent IP bans
- Maintain ethical scraping practices
- Reduce server costs for site owners

**Implementation Strategies:**

**Fixed Delay:**
```python
import time

def scrape_with_delay(urls, delay=2):
    """Scrape URLs with fixed delay"""
    results = []

    for url in urls:
        response = requests.get(url)
        results.append(response)

        # Wait before next request
        time.sleep(delay)

    return results
```

**Random Delay (More Human-like):**
```python
import random

def scrape_with_random_delay(urls, min_delay=1, max_delay=3):
    """Scrape with random delays"""
    results = []

    for url in urls:
        response = requests.get(url)
        results.append(response)

        # Random delay between min and max
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    return results
```

**Exponential Backoff:**
```python
def scrape_with_backoff(url, max_retries=3):
    """Retry with exponential backoff"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff: 1s, 2s, 4s, 8s...
            delay = 2 ** attempt
            print(f"Retry {attempt + 1} after {delay}s")
            time.sleep(delay)
```

**Rate Limiter Class:**
```python
import time
from collections import deque

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, requests_per_second=1):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()

    def acquire(self):
        """Wait until token is available"""
        while True:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(
                self.rate,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                break

            # Wait for next token
            time.sleep(0.1)

# Usage
limiter = RateLimiter(requests_per_second=2)

for url in urls:
    limiter.acquire()
    response = requests.get(url)
```

### 4. User Agent Management

**Why Use Proper User-Agent?**
- Identify your bot to website owners
- Provide contact information
- Avoid being blocked as suspicious traffic

**Good User-Agent Examples:**
```python
# Descriptive and contactable
"MyBot/1.0 (contact@example.com; Purpose: Research)"

# Identify organization
"UniversityBot/2.0 (university.edu; Academic research)"

# Mimic real browser (use sparingly)
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

**Implementation:**
```python
headers = {
    "User-Agent": "MyBot/1.0 (contact@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

response = requests.get(url, headers=headers)
```

**User-Agent Rotation (Advanced):**
```python
import random

USER_AGENTS = [
    "MyBot/1.0 (contact@example.com)",
    "MyBot/1.0 (Windows; contact@example.com)",
    "MyBot/1.0 (Linux; contact@example.com)",
]

def get_random_headers():
    """Get headers with random user agent"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }

response = requests.get(url, headers=get_random_headers())
```

## Technical Best Practices

### 1. Error Handling

**Comprehensive Error Handling:**
```python
import requests
from requests.exceptions import (
    RequestException,
    Timeout,
    HTTPError,
    ConnectionError,
    TooManyRedirects
)

def safe_scrape(url):
    """Scrape with comprehensive error handling"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    except Timeout:
        print(f"Timeout: {url}")
        return None

    except HTTPError as e:
        status_code = e.response.status_code

        if status_code == 404:
            print(f"Page not found: {url}")
        elif status_code == 403:
            print(f"Access forbidden: {url}")
        elif status_code == 429:
            print(f"Rate limited: {url}")
        elif status_code >= 500:
            print(f"Server error: {url}")

        return None

    except ConnectionError:
        print(f"Connection failed: {url}")
        return None

    except TooManyRedirects:
        print(f"Too many redirects: {url}")
        return None

    except RequestException as e:
        print(f"Request error: {url} - {e}")
        return None
```

### 2. Session Management

**Use Sessions for Multiple Requests:**
```python
# Session maintains connection pool and cookies
session = requests.Session()
session.headers.update({
    "User-Agent": "MyBot/1.0"
})

# Reuse session for multiple requests
for url in urls:
    response = session.get(url)
    # Process response
```

**Session with Retries:**
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create session with automatic retries"""
    session = requests.Session()

    # Configure retry strategy
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

# Usage
session = create_session()
response = session.get(url)
```

### 3. Data Validation

**Validate Scraped Data:**
```python
def validate_product(product_data):
    """Validate product data structure"""
    required_fields = ['name', 'price', 'url']

    # Check required fields exist
    for field in required_fields:
        if field not in product_data:
            return False, f"Missing field: {field}"

    # Validate field types
    if not isinstance(product_data['price'], (int, float)):
        return False, "Price must be numeric"

    if not product_data['url'].startswith('http'):
        return False, "Invalid URL"

    return True, "Valid"

# Usage
data = scrape_product(url)
is_valid, message = validate_product(data)

if is_valid:
    save_to_database(data)
else:
    log_error(f"Invalid data: {message}")
```

### 4. Caching

**Cache Responses to Avoid Redundant Requests:**
```python
import hashlib
import pickle
from pathlib import Path

class ResponseCache:
    """Simple file-based response cache"""

    def __init__(self, cache_dir=".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, url):
        """Generate cache file path from URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.pkl"

    def get(self, url):
        """Get cached response"""
        cache_path = self._get_cache_path(url)

        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                return pickle.load(f)

        return None

    def set(self, url, response):
        """Cache response"""
        cache_path = self._get_cache_path(url)

        with open(cache_path, 'wb') as f:
            pickle.dump(response, f)

# Usage
cache = ResponseCache()

def scrape_with_cache(url):
    # Check cache first
    cached = cache.get(url)
    if cached:
        print(f"Using cached response for {url}")
        return cached

    # Fetch fresh
    response = requests.get(url)
    cache.set(url, response)

    return response
```

### 5. Logging

**Implement Comprehensive Logging:**
```python
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now():%Y%m%d}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def scrape_with_logging(url):
    """Scrape with detailed logging"""
    logger.info(f"Starting scrape: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        logger.info(f"Success: {url} - Status: {response.status_code}")
        return response.text

    except Exception as e:
        logger.error(f"Failed: {url} - Error: {e}")
        return None
```

## Performance Optimization

### 1. Concurrent Scraping

**Threading (I/O Bound):**
```python
from concurrent.futures import ThreadPoolExecutor
import requests

def fetch_url(url):
    """Fetch single URL"""
    try:
        response = requests.get(url, timeout=10)
        return url, response.text
    except Exception as e:
        return url, None

def scrape_concurrent(urls, max_workers=5):
    """Scrape multiple URLs concurrently"""
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}

        for future in concurrent.futures.as_completed(future_to_url):
            url, content = future.result()
            results[url] = content

    return results
```

**Async/Await (Recommended):**
```python
import asyncio
import aiohttp

async def fetch_async(session, url):
    """Fetch URL asynchronously"""
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def scrape_async(urls):
    """Scrape multiple URLs asynchronously"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Usage
urls = ['https://example.com/page1', 'https://example.com/page2']
results = asyncio.run(scrape_async(urls))
```

### 2. Parsing Optimization

**Choose Right Parser:**
```python
# lxml - Fastest
soup = BeautifulSoup(html, 'lxml')

# html.parser - Built-in, no dependencies
soup = BeautifulSoup(html, 'html.parser')

# html5lib - Most lenient, slowest
soup = BeautifulSoup(html, 'html5lib')
```

**Use Specific Selectors:**
```python
# Slow - searches entire document
paragraphs = soup.find_all('p')

# Fast - searches within specific container
content = soup.find('div', class_='content')
paragraphs = content.find_all('p')
```

## When to Use Alternative Methods

### 1. Use Official APIs Instead

**Always prefer APIs when available:**
- More reliable than scraping
- Faster and more efficient
- Better structured data
- Officially supported

**Example:**
```python
# Instead of scraping Twitter
# Use Twitter API
import tweepy

api = tweepy.API(auth)
tweets = api.user_timeline(screen_name='@username', count=100)
```

### 2. Use Browser Automation for JavaScript

**When to use Selenium/Playwright:**
- Content loaded dynamically with JavaScript
- Need to interact with page (click, scroll, fill forms)
- Need to wait for specific elements
- AJAX requests load data

### 3. Use Headless Browsers

**When NOT to use headless browsers:**
- Static HTML content (use requests instead)
- Simple scraping tasks
- High-volume scraping (too slow)

## Troubleshooting

### Getting Blocked?

**Symptoms:**
- 403 Forbidden errors
- 429 Too Many Requests
- CAPTCHA challenges
- Empty responses

**Solutions:**
1. Slow down request rate
2. Use proper User-Agent
3. Respect robots.txt
4. Add random delays
5. Use session cookies
6. Rotate IP addresses (proxy)
7. Handle CAPTCHA properly

### JavaScript Content Not Loading?

**Solutions:**
1. Use Selenium/Playwright
2. Find API endpoints (check Network tab)
3. Analyze JavaScript code for data sources
4. Look for JSON in page source

### Parsing Errors?

**Solutions:**
1. Check HTML structure in browser DevTools
2. Use try-except for optional elements
3. Validate selectors
4. Handle malformed HTML with html5lib

## Checklist for Ethical Scraping

Before starting any scraping project:

- [ ] Check website's Terms of Service
- [ ] Read and respect robots.txt
- [ ] Implement rate limiting (at least 1-2 seconds between requests)
- [ ] Use descriptive User-Agent with contact info
- [ ] Implement proper error handling
- [ ] Log all activities
- [ ] Cache responses to avoid redundant requests
- [ ] Validate scraped data
- [ ] Handle personal data according to privacy laws
- [ ] Consider using official API if available
- [ ] Test with small sample before full scraping
- [ ] Monitor for changes that might break scraper
- [ ] Have permission if scraping behind authentication

## Legal Disclaimer

⚠️ **Important Notice:**

Web scraping legality varies by jurisdiction and specific circumstances. This guide is for educational purposes only and does not constitute legal advice.

**Before scraping:**
1. Consult with legal counsel
2. Review website's Terms of Service
3. Understand applicable laws (CFAA, GDPR, etc.)
4. Get permission when in doubt
5. Respect intellectual property rights

**This skill is provided for:**
- Educational purposes
- Research projects
- Personal use
- With explicit permission from site owners

**Do NOT use for:**
- Bypassing paywalls or authentication
- Violating Terms of Service
- Collecting personal data without consent
- Commercial purposes without permission
- Overloading servers

## Additional Resources

- OWASP Web Scraping Guide: https://owasp.org/
- robots.txt specification: https://www.robotstxt.org/
- Requests documentation: https://requests.readthedocs.io/
- BeautifulSoup documentation: https://www.crummy.com/software/BeautifulSoup/
- Scrapy Best Practices: https://docs.scrapy.org/
- Legal considerations: https://blog.apify.com/is-web-scraping-legal/
