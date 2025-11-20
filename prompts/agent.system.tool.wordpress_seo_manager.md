## wordpress_seo_manager tool

manage and update wordpress seo metadata and content

### important safety requirements
⚠️ ALWAYS require user confirmation before making changes
⚠️ ALL write operations require "confirmed": "true" in tool_args
⚠️ Review changes with user before execution

### authentication required
requires wordpress application password stored in memory:
- wp_username: wordpress username
- wp_app_password: wordpress application password (not regular password)

to create application password:
1. wordpress admin > users > profile
2. scroll to application passwords section
3. enter name and click add new
4. copy generated password
5. store using memory_save tool

### tool features
- update post titles slugs excerpts (meta descriptions)
- update post content with seo-optimized text
- assign categories and tags to posts
- bulk update image alt text for better image seo
- all changes logged and confirmed

### usage examples

update post meta (title excerpt slug):
```json
{
    "tool_name": "wordpress_seo_manager",
    "tool_args": {
        "action": "update_post_meta",
        "site_url": "https://example.com",
        "post_id": "123",
        "title": "SEO Optimized Title - Keyword Rich",
        "excerpt": "Compelling meta description with target keywords under 160 characters",
        "slug": "seo-friendly-url-slug",
        "confirmed": "true"
    }
}
```

update post content:
```json
{
    "tool_name": "wordpress_seo_manager",
    "tool_args": {
        "action": "update_post_content",
        "site_url": "https://example.com",
        "post_id": "123",
        "content": "<p>SEO optimized content with proper heading structure...</p>",
        "confirmed": "true"
    }
}
```

bulk update alt text:
```json
{
    "tool_name": "wordpress_seo_manager",
    "tool_args": {
        "action": "bulk_update_alt_text",
        "site_url": "https://example.com",
        "media_updates": [
            {"media_id": "45", "alt_text": "Descriptive alt text with keywords"},
            {"media_id": "46", "alt_text": "Another descriptive alt text"}
        ],
        "confirmed": "true"
    }
}
```

### seo best practices
- keep titles under 60 characters
- keep meta descriptions under 160 characters
- use descriptive keyword-rich alt text
- create readable seo-friendly url slugs
- maintain natural keyword density in content
- use proper heading hierarchy h1 h2 h3
