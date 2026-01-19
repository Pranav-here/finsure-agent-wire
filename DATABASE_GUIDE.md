# Database Guide

## Location
```
./data/autoposter.db
```

## Quick View Command
```bash
python scripts/view_db.py
```

## Database Structure

### Table: `posted_items`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-increment primary key |
| `url_hash` | TEXT | SHA-256 hash of canonical URL (for deduplication) |
| `canonical_url` | TEXT | Normalized URL |
| `original_url` | TEXT | Original source URL |
| `title` | TEXT | Article/video title |
| `source` | TEXT | Source type (arxiv, youtube, gdelt, rss) |
| `domain` | TEXT | Domain name |
| `published_at` | TEXT | When content was published |
| `posted_at` | TEXT | When posted to X |
| `relevance_score` | REAL | Calculated relevance score |

## Viewing Your Stats

Use the provided script to view statistics about your posted items:

```bash
python scripts/view_db.py
```

This will show:
- Total number of posts
- Breakdown by source (arXiv, YouTube, GDELT, RSS)
- Recent activity (last 24 hours, last 7 days)
- Highest scoring posts

## Viewing Options

### 1. Using the Script (Recommended)
```bash
python scripts/view_db.py
```

### 2. Using SQLite Command Line
```bash
# Open database
sqlite3 data/autoposter.db

# View all posts
SELECT id, title, source, relevance_score, posted_at 
FROM posted_items 
ORDER BY posted_at DESC;

# View posts by source
SELECT source, COUNT(*) as count 
FROM posted_items 
GROUP BY source;

# Exit
.quit
```

### 3. Using DB Browser for SQLite (GUI)
Download from: https://sqlitebrowser.org/

1. Download and install
2. Open `data/autoposter.db`
3. Browse visually

## Common Queries

### Get all arXiv posts
```sql
SELECT title, original_url, relevance_score 
FROM posted_items 
WHERE source = 'arxiv' 
ORDER BY posted_at DESC;
```

### Get highest scoring posts
```sql
SELECT title, source, relevance_score 
FROM posted_items 
ORDER BY relevance_score DESC 
LIMIT 10;
```

### Count posts by day
```sql
SELECT DATE(posted_at) as day, COUNT(*) as posts 
FROM posted_items 
GROUP BY day 
ORDER BY day DESC;
```

### Find duplicates (if any)
```sql
SELECT url_hash, COUNT(*) as count 
FROM posted_items 
GROUP BY url_hash 
HAVING count > 1;
```

## Notes

- The database automatically prevents duplicates using `url_hash`
- Posts are never deleted automatically
- The database grows over time (currently 24 KB for 4 posts)
- You can manually delete posts if needed using SQL `DELETE` commands
- Backup the database regularly if important

## Backup Command
```bash
# Copy database to backup
copy data\autoposter.db data\autoposter_backup.db
```

## Reset Database
If you want to start fresh:
```bash
# Delete database (will be recreated on next run)
del data\autoposter.db
```
