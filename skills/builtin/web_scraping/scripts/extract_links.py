#!/usr/bin/env python3
"""
Extract all links from a web page
Uses _skill_args injected by skills_tool

Args:
    url (str): URL to scrape (required)
    filter_domain (str): Only include links from this domain (optional)
    include_external (bool): Include external links (default: True)
    include_anchors (bool): Include anchor links (#) (default: False)
    user_agent (str): Custom User-Agent string (optional)
    timeout (int): Request timeout in seconds (default: 10)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urlparse, urljoin
from collections import defaultdict

# Args injected by skills_tool
url = _skill_args.get("url")
filter_domain = _skill_args.get("filter_domain", None)
include_external = _skill_args.get("include_external", True)
include_anchors = _skill_args.get("include_anchors", False)
user_agent = _skill_args.get("user_agent", "Mozilla/5.0 (compatible; AgentZero/1.0; Educational)")
timeout = _skill_args.get("timeout", 10)

def extract_links(url, filter_domain=None, include_external=True, include_anchors=False, user_agent=None, timeout=10):
    """
    Extract all links from a web page

    Args:
        url: URL to scrape
        filter_domain: Only include links from this domain
        include_external: Include external links
        include_anchors: Include anchor links
        user_agent: User-Agent header
        timeout: Request timeout

    Returns:
        dict with categorized links
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        # Make request
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        parsed_base = urlparse(url)
        base_domain = parsed_base.netloc

        # Initialize result structure
        result = {
            "source_url": url,
            "base_domain": base_domain,
            "internal_links": [],
            "external_links": [],
            "anchor_links": [],
            "email_links": [],
            "tel_links": [],
            "other_links": [],
            "statistics": {
                "total": 0,
                "internal": 0,
                "external": 0,
                "anchors": 0,
                "emails": 0,
                "tel": 0,
                "other": 0,
                "broken_links": 0
            }
        }

        # Extract all links
        all_links = soup.find_all('a', href=True)
        print(f"Found {len(all_links)} total links")

        # Process each link
        for link_tag in all_links:
            href = link_tag['href'].strip()
            link_text = link_tag.text.strip()

            # Skip empty links
            if not href:
                continue

            # Handle different link types
            if href.startswith('mailto:'):
                result["email_links"].append({
                    "url": href,
                    "text": link_text,
                    "email": href.replace('mailto:', '')
                })
                result["statistics"]["emails"] += 1

            elif href.startswith('tel:'):
                result["tel_links"].append({
                    "url": href,
                    "text": link_text,
                    "phone": href.replace('tel:', '')
                })
                result["statistics"]["tel"] += 1

            elif href.startswith('#'):
                if include_anchors:
                    result["anchor_links"].append({
                        "anchor": href,
                        "text": link_text
                    })
                    result["statistics"]["anchors"] += 1

            elif href.startswith(('http://', 'https://', '//')):
                # Absolute URL or protocol-relative URL
                if href.startswith('//'):
                    href = parsed_base.scheme + ':' + href

                parsed_link = urlparse(href)

                # Check if internal or external
                if parsed_link.netloc == base_domain:
                    # Internal link
                    result["internal_links"].append({
                        "url": href,
                        "text": link_text,
                        "path": parsed_link.path
                    })
                    result["statistics"]["internal"] += 1
                else:
                    # External link
                    if include_external:
                        # Apply domain filter if specified
                        if filter_domain and filter_domain not in parsed_link.netloc:
                            continue

                        result["external_links"].append({
                            "url": href,
                            "text": link_text,
                            "domain": parsed_link.netloc
                        })
                        result["statistics"]["external"] += 1

            elif href.startswith('/'):
                # Root-relative URL
                absolute_url = urljoin(url, href)
                result["internal_links"].append({
                    "url": absolute_url,
                    "text": link_text,
                    "path": href
                })
                result["statistics"]["internal"] += 1

            elif href.startswith(('javascript:', 'data:', '#')):
                # Skip javascript:, data:, and plain anchors (if not including)
                continue

            else:
                # Relative URL or other
                try:
                    absolute_url = urljoin(url, href)
                    parsed_link = urlparse(absolute_url)

                    if parsed_link.netloc == base_domain:
                        result["internal_links"].append({
                            "url": absolute_url,
                            "text": link_text,
                            "path": parsed_link.path
                        })
                        result["statistics"]["internal"] += 1
                    else:
                        result["other_links"].append({
                            "url": href,
                            "text": link_text
                        })
                        result["statistics"]["other"] += 1
                except Exception as e:
                    result["other_links"].append({
                        "url": href,
                        "text": link_text,
                        "error": str(e)
                    })
                    result["statistics"]["other"] += 1

        # Calculate total
        result["statistics"]["total"] = sum([
            result["statistics"]["internal"],
            result["statistics"]["external"],
            result["statistics"]["anchors"],
            result["statistics"]["emails"],
            result["statistics"]["tel"],
            result["statistics"]["other"]
        ])

        # Remove duplicates while preserving order
        result["internal_links"] = list({link['url']: link for link in result["internal_links"]}.values())
        result["external_links"] = list({link['url']: link for link in result["external_links"]}.values())

        # Update counts after deduplication
        result["statistics"]["internal"] = len(result["internal_links"])
        result["statistics"]["external"] = len(result["external_links"])

        return result

    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout} seconds"}

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        return {"error": f"HTTP error {status_code}"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}

    except Exception as e:
        return {"error": f"Processing failed: {str(e)}"}

# Main execution
if not url:
    print("Error: 'url' is required in script_args")
    print("\nUsage:")
    print(json.dumps({
        "tool_name": "skills_tool",
        "tool_args": {
            "method": "execute_script",
            "skill_name": "web_scraping",
            "script_path": "scripts/extract_links.py",
            "script_args": {
                "url": "https://example.com",
                "filter_domain": "example.com",  # optional
                "include_external": True,  # optional
                "include_anchors": False  # optional
            }
        }
    }, indent=2))
    exit(1)

# Validate URL
if not url.startswith(('http://', 'https://')):
    print(f"Error: Invalid URL '{url}'. Must start with http:// or https://")
    exit(1)

print("=" * 60)
print("LINK EXTRACTION")
print("=" * 60)
print(f"Source: {url}")
if filter_domain:
    print(f"Filter: Only links from '{filter_domain}'")
print(f"Include External: {include_external}")
print(f"Include Anchors: {include_anchors}")
print("=" * 60)
print()

# Add polite delay
time.sleep(1)

# Extract links
result = extract_links(url, filter_domain, include_external, include_anchors, user_agent, timeout)

# Output results
if "error" in result:
    print(f"\n❌ Error: {result['error']}")
    exit(1)

print("\n" + "=" * 60)
print("EXTRACTION RESULTS")
print("=" * 60)

stats = result["statistics"]
print(f"\nStatistics:")
print(f"  Total Links: {stats['total']}")
print(f"  Internal: {stats['internal']}")
print(f"  External: {stats['external']}")
if include_anchors:
    print(f"  Anchors: {stats['anchors']}")
print(f"  Email: {stats['emails']}")
print(f"  Tel: {stats['tel']}")
if stats['other'] > 0:
    print(f"  Other: {stats['other']}")

# Show internal links
if result["internal_links"]:
    print(f"\n--- Internal Links ({len(result['internal_links'])}) ---")
    for i, link in enumerate(result["internal_links"][:20], 1):  # Show first 20
        print(f"{i}. {link['url']}")
        if link['text']:
            print(f"   Text: {link['text'][:60]}")

# Show external links
if result["external_links"]:
    print(f"\n--- External Links ({len(result['external_links'])}) ---")
    for i, link in enumerate(result["external_links"][:20], 1):  # Show first 20
        print(f"{i}. {link['url']}")
        if link['text']:
            print(f"   Text: {link['text'][:60]}")

# Show email links
if result["email_links"]:
    print(f"\n--- Email Links ({len(result['email_links'])}) ---")
    for i, link in enumerate(result["email_links"], 1):
        print(f"{i}. {link['email']}")
        if link['text']:
            print(f"   Text: {link['text']}")

# Show anchor links
if include_anchors and result["anchor_links"]:
    print(f"\n--- Anchor Links ({len(result['anchor_links'])}) ---")
    for i, link in enumerate(result["anchor_links"][:10], 1):  # Show first 10
        print(f"{i}. {link['anchor']} - {link['text'][:40]}")

print("\n" + "=" * 60)
print("✓ Link extraction completed successfully")
print("=" * 60)

# Output as JSON for programmatic use
print("\nJSON Output (full results):")
print(json.dumps(result, indent=2, ensure_ascii=False))
