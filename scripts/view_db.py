"""View database contents and statistics."""

import sqlite3
from pathlib import Path
from datetime import datetime

def view_database():
    """Display database contents and statistics."""
    db_path = Path(__file__).parent.parent / "data" / "autoposter.db"
    
    if not db_path.exists():
        print(f"[ERROR] Database not found at: {db_path}")
        return
    
    print(f"Database Location: {db_path}")
    print(f"Size: {db_path.stat().st_size / 1024:.2f} KB\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get schema
    print("=" * 80)
    print("DATABASE SCHEMA")
    print("=" * 80)
    cursor.execute("PRAGMA table_info(posted_items)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:20s} {col[2]:15s} {'NOT NULL' if col[3] else 'NULL'}")
    
    # Get total count
    cursor.execute("SELECT COUNT(*) FROM posted_items")
    total_count = cursor.fetchone()[0]
    print(f"\n{'-' * 80}")
    print(f"TOTAL POSTS: {total_count}")
    print(f"{'-' * 80}\n")
    
    # Get posts by source
    print("=" * 80)
    print("POSTS BY SOURCE")
    print("=" * 80)
    cursor.execute("""
        SELECT source, COUNT(*) as count 
        FROM posted_items 
        GROUP BY source 
        ORDER BY count DESC
    """)
    for source, count in cursor.fetchall():
        print(f"  {source:20s} {count:5d} posts")
    
    # Get recent posts
    print(f"\n{'=' * 80}")
    print("10 MOST RECENT POSTS")
    print("=" * 80)
    cursor.execute("""
        SELECT id, original_url, title, source, relevance_score, posted_at, url_hash 
        FROM posted_items 
        ORDER BY posted_at DESC 
        LIMIT 10
    """)
    
    posts = cursor.fetchall()
    
    if not posts:
        print("  (No posts yet)")
    else:
        for i, post in enumerate(posts, 1):
            post_id, url, title, source, score, posted_at, url_hash = post
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = posted_at
            
            # Remove emojis and special characters for Windows console
            title_clean = title.encode('ascii', 'ignore').decode('ascii')
            url_clean = url.encode('ascii', 'ignore').decode('ascii')
            
            print(f"\n#{i} - ID: {post_id}")
            print(f"  Title: {title_clean[:80]}...")
            print(f"  URL: {url_clean}")
            print(f"  Source: {source}")
            print(f"  Score: {score}")
            print(f"  Posted: {time_str}")
            print(f"  URL Hash: {url_hash[:16]}...")
    
    # Get posts in last 24 hours
    print(f"\n{'=' * 80}")
    print("POSTS IN LAST 24 HOURS")
    print("=" * 80)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM posted_items 
        WHERE datetime(posted_at) > datetime('now', '-1 day')
    """)
    recent_count = cursor.fetchone()[0]
    print(f"  Total: {recent_count} posts")
    
    # Get posts in last 7 days
    cursor.execute("""
        SELECT COUNT(*) 
        FROM posted_items 
        WHERE datetime(posted_at) > datetime('now', '-7 days')
    """)
    week_count = cursor.fetchone()[0]
    print(f"  Last 7 days: {week_count} posts")
    
    conn.close()
    
    print(f"\n{'=' * 80}")
    print("[SUCCESS] Database view complete!")
    print("=" * 80)

if __name__ == "__main__":
    view_database()
