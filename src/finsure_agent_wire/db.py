"""Database operations for deduplication and state tracking."""

import hashlib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Set
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from .models import NewsItem

logger = logging.getLogger(__name__)


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL by:
    1. Normalizing scheme (http -> https where appropriate)
    2. Removing tracking parameters (utm_*, fbclid, etc.)
    3. Removing trailing slashes
    4. Lowercasing domain
    
    Args:
        url: Original URL
        
    Returns:
        Canonicalized URL
    """
    try:
        parsed = urlparse(url)
        
        # Lowercase domain
        netloc = parsed.netloc.lower()
        
        # Remove tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid',
            'mc_cid', 'mc_eid',  # Mailchimp
            '_ga', '_gl',  # Google Analytics
            'ref', 'referer', 'referrer',
        }
        
        # Parse and filter query params
        query_params = parse_qs(parsed.query)
        clean_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in tracking_params
        }
        
        # Rebuild query string
        clean_query = urlencode(clean_params, doseq=True) if clean_params else ''
        
        # Remove trailing slash from path
        path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
        
        # Prefer https over http for common domains
        scheme = parsed.scheme
        if scheme == 'http' and netloc in {'www.youtube.com', 'medium.com', 'techcrunch.com'}:
            scheme = 'https'
        
        # Rebuild URL
        canonical = urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))
        
        return canonical
    
    except Exception as e:
        logger.warning(f"Error canonicalizing URL {url}: {e}")
        return url


def hash_url(url: str) -> str:
    """
    Generate SHA-256 hash of URL for deduplication.
    
    Args:
        url: URL to hash (should be canonicalized first)
        
    Returns:
        Hex digest of hash
    """
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


class Database:
    """SQLite database for tracking posted items and preventing duplicates."""
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Table for tracking posted items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posted_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                canonical_url TEXT NOT NULL,
                original_url TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                domain TEXT,
                published_at TEXT NOT NULL,
                posted_at TEXT NOT NULL,
                relevance_score REAL
            )
        """)
        
        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_hash 
            ON posted_items(url_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posted_at 
            ON posted_items(posted_at)
        """)
        
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_posted_url_hashes(self) -> Set[str]:
        """
        Get set of all URL hashes that have been posted.
        
        Returns:
            Set of URL hashes
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT url_hash FROM posted_items")
        return {row['url_hash'] for row in cursor.fetchall()}
    
    def mark_as_posted(self, item: NewsItem) -> None:
        """
        Mark an item as posted.
        
        Args:
            item: NewsItem that was posted
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO posted_items (
                    url_hash, canonical_url, original_url, title,
                    source, domain, published_at, posted_at, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.url_hash,
                item.canonical_url,
                item.url,
                item.title,
                item.source,
                item.domain,
                item.published_at.isoformat(),
                datetime.now().isoformat(),
                item.relevance_score,
            ))
            self.conn.commit()
            logger.debug(f"Marked as posted: {item.canonical_url}")
        
        except sqlite3.IntegrityError:
            # Already posted (duplicate hash)
            logger.warning(f"Attempted to mark duplicate as posted: {item.canonical_url}")
    
    def get_stats(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with stats
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM posted_items")
        total = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM posted_items 
            GROUP BY source
        """)
        by_source = {row['source']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM posted_items 
            WHERE posted_at >= datetime('now', '-7 days')
        """)
        last_7_days = cursor.fetchone()['count']
        
        return {
            'total_posted': total,
            'by_source': by_source,
            'last_7_days': last_7_days,
        }
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")


def prepare_items_for_dedup(items: List[NewsItem]) -> List[NewsItem]:
    """
    Prepare items for deduplication by canonicalizing URLs and generating hashes.
    
    Args:
        items: List of NewsItems
        
    Returns:
        Same list with canonical_url and url_hash fields populated
    """
    for item in items:
        item.canonical_url = canonicalize_url(item.url)
        item.url_hash = hash_url(item.canonical_url)
    
    return items


def deduplicate_items(items: List[NewsItem], db: Database) -> List[NewsItem]:
    """
    Remove items that have already been posted and collapse duplicates
    within the current batch, keeping the strongest candidate.
    
    Args:
        items: List of NewsItems (must have url_hash populated)
        db: Database instance
        
    Returns:
        Filtered list of items not yet posted
    """
    posted_hashes = db.get_posted_url_hashes()
    
    kept_by_hash = {}
    skipped_posted = 0
    
    for item in items:
        if item.url_hash in posted_hashes:
            skipped_posted += 1
            continue
        
        existing = kept_by_hash.get(item.url_hash)
        # Prefer higher relevance, then newer publish time
        if (
            existing is None
            or (
                item.relevance_score,
                item.published_at.timestamp(),
            )
            > (
                existing.relevance_score,
                existing.published_at.timestamp(),
            )
        ):
            kept_by_hash[item.url_hash] = item
    
    in_batch_duplicates = len(items) - skipped_posted - len(kept_by_hash)
    
    if skipped_posted:
        logger.info(f"Removed {skipped_posted} items already posted (DB dedup)")
    if in_batch_duplicates:
        logger.info(f"Collapsed {in_batch_duplicates} duplicates within current batch")
    
    return list(kept_by_hash.values())
