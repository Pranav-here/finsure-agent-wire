"""Main pipeline orchestration for news collection, scoring, and posting."""

import logging
from collections import Counter
from typing import List

from .config import Config
from .db import Database, prepare_items_for_dedup, deduplicate_items
from .models import NewsItem
from .scoring import score_items
from .sources import fetch_gdelt_articles, fetch_youtube_videos, fetch_rss_feeds
from .x_client import XClient

logger = logging.getLogger(__name__)


def collect_news(config: Config) -> List[NewsItem]:
    """
    Collect news from all configured sources.
    
    Args:
        config: Application configuration
        
    Returns:
        List of all collected NewsItems
    """
    logger.info("=== Starting News Collection ===")
    
    all_items = []
    
    # GDELT
    try:
        gdelt_items = fetch_gdelt_articles(
            lookback_hours=config.lookback_hours,
            max_records=config.gdelt_max_records,
        )
        all_items.extend(gdelt_items)
        logger.info(f"GDELT: Fetched {len(gdelt_items)} articles")
    except Exception as e:
        logger.error(f"GDELT fetch failed: {e}")
    
    # YouTube
    if config.youtube_api_key:
        try:
            youtube_items = fetch_youtube_videos(
                api_key=config.youtube_api_key,
                queries=config.get_youtube_query_list(),
                lookback_hours=config.lookback_hours,
            )
            all_items.extend(youtube_items)
            logger.info(f"YouTube: Fetched {len(youtube_items)} videos")
        except Exception as e:
            logger.error(f"YouTube fetch failed: {e}")
    else:
        logger.info("YouTube: Skipped (no API key)")
    
    # RSS
    rss_feeds = config.get_rss_feed_list()
    if rss_feeds:
        try:
            rss_items = fetch_rss_feeds(
                feed_urls=rss_feeds,
                lookback_hours=config.lookback_hours,
            )
            all_items.extend(rss_items)
            logger.info(f"RSS: Fetched {len(rss_items)} items")
        except Exception as e:
            logger.error(f"RSS fetch failed: {e}")
    else:
        logger.info("RSS: Skipped (no feeds configured)")
    
    logger.info(f"Total items collected: {len(all_items)}")
    return all_items


def filter_and_score(items: List[NewsItem], config: Config) -> List[NewsItem]:
    """
    Score items and filter by relevance threshold.
    
    Args:
        items: List of NewsItems
        config: Application configuration
        
    Returns:
        Filtered and scored list
    """
    logger.info("=== Scoring and Filtering ===")
    
    # Score all items
    scored_items = score_items(
        items,
        agent_weight=config.agent_keyword_weight,
        finance_weight=config.finance_keyword_weight,
        recency_weight=config.recency_weight,
    )
    
    # Filter by minimum score
    before_count = len(scored_items)
    relevant_items = [
        item for item in scored_items 
        if item.relevance_score >= config.min_score_threshold
    ]
    after_count = len(relevant_items)
    
    filtered_count = before_count - after_count
    logger.info(
        f"Filtered by relevance: {after_count} items passed (threshold >= {config.min_score_threshold}), "
        f"{filtered_count} filtered out"
    )
    
    return relevant_items


def rank_items(items: List[NewsItem]) -> List[NewsItem]:
    """
    Rank items by score (descending) then recency (descending).
    
    Args:
        items: List of NewsItems with scores
        
    Returns:
        Sorted list
    """
    # Sort by score DESC, then by published_at DESC
    sorted_items = sorted(
        items,
        key=lambda x: (-x.relevance_score, -x.published_at.timestamp())
    )
    
    return sorted_items


def select_items_to_post(
    items: List[NewsItem],
    config: Config,
) -> List[NewsItem]:
    """
    Select top items to post, respecting rate limits.
    
    Args:
        items: Sorted list of NewsItems
        config: Application configuration
        
    Returns:
        Items to post (respects max_posts_per_run and max_posts_per_domain)
    """
    selected = []
    domain_counts = Counter()
    
    for item in items:
        # Check global limit
        if len(selected) >= config.max_posts_per_run:
            break
        
        # Check per-domain limit
        if domain_counts[item.domain] >= config.max_posts_per_domain:
            logger.debug(f"Skipping {item.url} (domain limit reached for {item.domain})")
            continue
        
        selected.append(item)
        domain_counts[item.domain] += 1
    
    logger.info(f"Selected {len(selected)} items to post (max={config.max_posts_per_run})")
    return selected


def post_items(
    items: List[NewsItem],
    config: Config,
    db: Database,
) -> int:
    """
    Post items to X (Twitter).
    
    Args:
        items: Items to post
        config: Application configuration
        db: Database for tracking posted items
        
    Returns:
        Number of items successfully posted
    """
    if config.review_mode:
        logger.info("=== REVIEW MODE: Tweet Drafts ===")
        for i, item in enumerate(items, 1):
            tweet = item.format_tweet()
            logger.info(f"\n--- Draft {i}/{len(items)} ---")
            logger.info(f"Title: {item.title}")
            logger.info(f"URL: {item.canonical_url or item.url}")
            logger.info(f"Score: {item.relevance_score:.1f}")
            logger.info(f"Tweet:\n{tweet}")
            logger.info(f"Length: {len(tweet)}/280")
        logger.info(f"\nREVIEW MODE: Would post {len(items)} tweets (not actually posting)")
        return 0
    
    if config.dry_run:
        logger.info(f"DRY_RUN mode: Would post {len(items)} tweets (not actually posting)")
        for i, item in enumerate(items, 1):
            tweet = item.format_tweet()
            logger.info(f"[DRY RUN {i}] {tweet[:100]}... (score={item.relevance_score:.1f})")
        return 0
    
    # Live posting
    logger.info("=== Posting to X ===")
    
    try:
        x_client = XClient(
            api_key=config.x_api_key,
            api_secret=config.x_api_secret,
            access_token=config.x_access_token,
            access_secret=config.x_access_secret,
        )
        
        # Verify credentials first
        x_client.verify_credentials()
    
    except Exception as e:
        logger.error(f"X client initialization failed: {e}")
        return 0
    
    posted_count = 0
    
    for item in items:
        try:
            tweet = item.format_tweet()
            logger.info(f"Posting: {tweet[:80]}...")
            
            x_client.create_tweet(tweet)
            
            # Mark as posted in database
            db.mark_as_posted(item)
            
            posted_count += 1
            logger.info(f"Posted {posted_count}/{len(items)}")
        
        except Exception as e:
            logger.error(f"Failed to post tweet for {item.url}: {e}")
            # Continue with next item
            continue
    
    logger.info(f"Successfully posted {posted_count}/{len(items)} tweets")
    return posted_count


def run_pipeline(config: Config) -> None:
    """
    Run the complete pipeline: collect, score, dedupe, rank, post.
    
    Args:
        config: Application configuration
    """
    logger.info("=== AI Agents in Finance News Autoposter ===")
    logger.info(f"DRY_RUN: {config.dry_run}")
    logger.info(f"REVIEW_MODE: {config.review_mode}")
    logger.info(f"Lookback: {config.lookback_hours} hours")
    logger.info(f"Max posts: {config.max_posts_per_run}")
    logger.info(f"Min score: {config.min_score_threshold}")
    
    # Initialize database
    db = Database(config.db_path)
    
    try:
        # 1. Collect
        items = collect_news(config)
        
        if not items:
            logger.warning("No items collected from any source. Exiting.")
            return
        
        # 2. Score and filter
        relevant_items = filter_and_score(items, config)
        
        if not relevant_items:
            logger.warning("No items passed relevance filter. Exiting.")
            return
        
        # 3. Prepare for deduplication
        prepare_items_for_dedup(relevant_items)
        
        # 4. Deduplicate
        unique_items = deduplicate_items(relevant_items, db)
        
        if not unique_items:
            logger.info("All items were duplicates (already posted). Exiting.")
            return
        
        # 5. Rank
        ranked_items = rank_items(unique_items)
        
        # 6. Select top items
        items_to_post = select_items_to_post(ranked_items, config)
        
        if not items_to_post:
            logger.info("No items selected for posting (domain limits or empty). Exiting.")
            return
        
        # 7. Post
        posted_count = post_items(items_to_post, config, db)
        
        # 8. Summary
        logger.info("=== Pipeline Complete ===")
        logger.info(f"Collected: {len(items)}")
        logger.info(f"Relevant: {len(relevant_items)}")
        logger.info(f"Unique: {len(unique_items)}")
        logger.info(f"Posted: {posted_count}")
        
        # Database stats
        stats = db.get_stats()
        logger.info(f"Database stats: {stats}")
    
    finally:
        db.close()
