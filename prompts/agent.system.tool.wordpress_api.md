## wordpress_api tool

fetch wordpress site data via rest api

### tool features
- get site information name description url
- fetch posts with seo metadata yoast rankmath
- fetch pages and page hierarchy
- get specific post or page with full content
- retrieve categories and tags
- fetch media items and check alt text optimization
- search content across site

### authentication
- public endpoints work without auth
- for private data user must provide wordpress application password
- store credentials using agent memory: wp_username wp_app_password

### usage examples

get site info:
```json
{
    "tool_name": "wordpress_api",
    "tool_args": {
        "action": "get_site_info",
        "site_url": "https://example.com"
    }
}
```

fetch posts with seo data:
```json
{
    "tool_name": "wordpress_api",
    "tool_args": {
        "action": "get_posts",
        "site_url": "https://example.com"
    }
}
```

get specific post:
```json
{
    "tool_name": "wordpress_api",
    "tool_args": {
        "action": "get_post",
        "site_url": "https://example.com",
        "post_id": "123"
    }
}
```

search content:
```json
{
    "tool_name": "wordpress_api",
    "tool_args": {
        "action": "search_content",
        "site_url": "https://example.com",
        "search_query": "keyword research"
    }
}
```

### seo integration
- automatically extracts yoast seo metadata when available
- includes title description canonical og tags
- useful for analyzing current seo optimization status
