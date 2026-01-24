---
description: Manually trigger lead discovery from configured platforms (Reddit, Stack Overflow, HackerNews, Dev.to)
argument-hint: [organization-id] [--platform reddit|stackoverflow|hackernews|devto|all]
allowed-tools: [Bash, Read, Write, Glob]
---

# Manual Lead Discovery

Trigger lead discovery for a specific organization and optionally filter by platform.

## Usage

```bash
/leads/discover [organization-id] [--platform <platform-type>]
```

## Arguments

- `organization-id`: The organization UUID to discover leads for (required)
- `--platform`: Filter by specific platform (optional)
  - `reddit`: Reddit discovery only
  - `stackoverflow`: Stack Overflow discovery only
  - `hackernews`: HackerNews discovery only
  - `devto`: Dev.to discovery only
  - `all`: All configured platforms (default)

## Examples

```bash
# Discover from all platforms
/leads/discover 550e8400-e29b-41d4-a716-446655440000

# Discover from Reddit only
/leads/discover 550e8400-e29b-41d4-a716-446655440000 --platform reddit

# Discover from Stack Overflow
/leads/discover 550e8400-e29b-41d4-a716-446655440000 --platform stackoverflow
```

## Implementation Steps

1. Validate organization ID exists in database
2. Load active platform sources for organization
3. Execute discovery from specified platform(s)
4. Display results (total discovered, by platform, qualified count)
5. Queue discovered leads for AI qualification

## Expected Output

```
🔎 Starting manual lead discovery...
📋 Organization: Mahoosuc Solutions (550e8400-e29b-41d4-a716-446655440000)
🌐 Platforms: reddit, stackoverflow, hackernews, devto

✅ Discovery Results:
   - Reddit: 8 leads discovered
   - Stack Overflow: 12 leads discovered
   - HackerNews: 3 leads discovered
   - Dev.to: 5 leads discovered

📊 Total: 28 leads discovered
🤖 Queued 28 leads for AI qualification

✅ Discovery complete!
```

## Notes

- Discovery respects platform rate limits
- Deduplication is automatic (content hash matching)
- Leads are queued for AI qualification via Redis pub/sub
- Results can be viewed in lead_contacts table after qualification
