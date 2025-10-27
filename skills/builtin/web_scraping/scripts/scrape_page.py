#!/usr/bin/env python3
"""
Basic web page scraper with BeautifulSoup
Uses _skill_args injected by skills_tool

Args:
    url (str): URL to scrape (required)
    selector (str): CSS selector to extract specific elements (optional)
    user_agent (str): Custom User-Agent string (optional)
    timeout (int): Request timeout in seconds (default: 10)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlparse

# Args injected by skills_tool
url = _skill_args.get("url")
selector = _skill_args.get("selector", None)
user_agent = _skill_args.get("user_agent", "Mozilla/5.0 (compatible; AgentZero/1.0; Educational)")
timeout = _skill_args.get("timeout", 10)

def check_robots_txt(url):
    """Check if URL is allowed by robots.txt"""
    try:
        from urllib.robotparser import RobotFileParser
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        allowed = rp.can_fetch(user_agent, url)
        return allowed, robots_url
    except Exception as e:
        # If robots.txt check fails, proceed with caution
        return True, f"Could not verify robots.txt: {e}"

def scrape_page(url, selector=None, user_agent=None, timeout=10):
    """
    Scrape web page content

    Args:
        url: URL to scrape
        selector: CSS selector for specific elements
        user_agent: User-Agent header
        timeout: Request timeout

    Returns:
        dict with scraped data
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # Make request
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        result = {
            "url": url,
            "status_code": response.status_code,
            "content_type": response.headers.get('Content-Type', 'unknown'),
            "page_title": None,
            "data": []
        }

        # Extract page title
        title_tag = soup.find('title')
        if title_tag:
            result["page_title"] = title_tag.text.strip()

        if selector:
            # Extract specific elements using selector
            elements = soup.select(selector)
            print(f"\nFound {len(elements)} elements matching '{selector}'")

            for elem in elements:
                result["data"].append({
                    "tag": elem.name,
                    "text": elem.text.strip(),
                    "html": str(elem)[:200]  # First 200 chars of HTML
                })

        else:
            # Extract general page info
            result["meta_description"] = None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                result["meta_description"] = meta_desc.get('content', '')

            # Extract headings
            headings = []
            for tag in ['h1', 'h2', 'h3']:
                for heading in soup.find_all(tag):
                    headings.append({
                        "level": tag,
                        "text": heading.text.strip()
                    })
            result["headings"] = headings[:10]  # First 10 headings

            # Count links
            links = soup.find_all('a', href=True)
            result["link_count"] = len(links)

            # Count images
            images = soup.find_all('img')
            result["image_count"] = len(images)

        return result

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout} seconds"}

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_msg = {
            404: "Page not found (404)",
            403: "Access forbidden (403) - check robots.txt compliance",
            429: "Rate limited (429) - too many requests",
            500: "Server error (500)",
            503: "Service unavailable (503)"
        }.get(status_code, f"HTTP error {status_code}")

        return {"error": error_msg}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}"}

# Main execution
if not url:
    print("Error: 'url' is required in script_args")
    print("\nUsage:")
    print(json.dumps({
        "tool_name": "skills_tool",
        "tool_args": {
            "method": "execute_script",
            "skill_name": "web_scraping",
            "script_path": "scripts/scrape_page.py",
            "script_args": {
                "url": "https://example.com",
                "selector": "h1, p",  # optional
                "timeout": 10  # optional
            }
        }
    }, indent=2))
    exit(1)

# Validate URL
if not url.startswith(('http://', 'https://')):
    print(f"Error: Invalid URL '{url}'. Must start with http:// or https://")
    exit(1)

# Check robots.txt
print("=" * 60)
print("ETHICAL SCRAPING CHECK")
print("=" * 60)
allowed, robots_info = check_robots_txt(url)
if isinstance(robots_info, str) and robots_info.startswith("Could not"):
    print(f"⚠️  {robots_info}")
    print("Proceeding with caution...")
elif allowed:
    print(f"✓ URL is allowed by robots.txt")
else:
    print(f"✗ URL is DISALLOWED by robots.txt")
    print(f"Robots.txt: {robots_info}")
    print("\n⚠️  Ethical scraping recommendation: Do NOT scrape this URL")
    print("Exiting to respect site's robots.txt")
    exit(1)

print(f"User-Agent: {user_agent}")
print("=" * 60)
print()

# Add polite delay
time.sleep(1)

# Scrape the page
result = scrape_page(url, selector, user_agent, timeout)

# Output results
if "error" in result:
    print(f"\n❌ Error: {result['error']}")
    exit(1)

print("\n" + "=" * 60)
print("SCRAPING RESULTS")
print("=" * 60)
print(f"\nURL: {result['url']}")
print(f"Status: {result['status_code']}")
print(f"Content-Type: {result['content_type']}")

if result.get('page_title'):
    print(f"Title: {result['page_title']}")

if selector:
    print(f"\nExtracted {len(result['data'])} elements:")
    for i, item in enumerate(result['data'][:20], 1):  # Show first 20
        print(f"\n{i}. <{item['tag']}>")
        print(f"   Text: {item['text'][:100]}...")
else:
    if result.get('meta_description'):
        print(f"Description: {result['meta_description'][:150]}...")

    if result.get('headings'):
        print(f"\nHeadings ({len(result['headings'])} found):")
        for h in result['headings'][:5]:
            print(f"  {h['level']}: {h['text'][:80]}")

    print(f"\nPage Statistics:")
    print(f"  Links: {result.get('link_count', 0)}")
    print(f"  Images: {result.get('image_count', 0)}")

print("\n" + "=" * 60)
print("✓ Scraping completed successfully")
print("=" * 60)

# Output as JSON for programmatic use
print("\nJSON Output:")
print(json.dumps(result, indent=2, ensure_ascii=False))
