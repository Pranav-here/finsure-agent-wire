"""arXiv research paper collector for AI + Finance."""

import logging
from datetime import datetime, timezone, timedelta
from typing import List
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from ..models import NewsItem

logger = logging.getLogger(__name__)


def fetch_arxiv_papers(
    queries: List[str],
    lookback_hours: int = 24,
    max_results: int = 50
) -> List[NewsItem]:
    """
    Fetch recent papers from arXiv matching AI + finance topics.
    
    Args:
        queries: List of search queries
        lookback_hours: Only include papers from last N hours
        max_results: Maximum papers per query
        
    Returns:
        List of NewsItems representing research papers
    """
    if not queries:
        logger.info("No arXiv queries configured, skipping arXiv fetch")
        return []
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    all_items = []
    
    for query in queries:
        try:
            logger.info(f"Searching arXiv for: {query}")
            
            # arXiv API endpoint
            base_url = "http://export.arxiv.org/api/query?"
            
            # Build query parameters
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            url = base_url + urllib.parse.urlencode(params)
            
            # Fetch results
            with urllib.request.urlopen(url) as response:
                xml_data = response.read()
            
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # Namespace for Atom feed
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            logger.info(f"arXiv returned {len(entries)} papers for query: {query}")
            
            for entry in entries:
                try:
                    # Get publication date
                    published_str = entry.find('atom:published', ns).text
                    pub_date = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    
                    # Filter by cutoff
                    if pub_date < cutoff:
                        continue
                    
                    # Get title
                    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                    
                    # Get abstract
                    summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                    
                    # Get URL
                    link = entry.find('atom:id', ns).text
                    
                    # Get authors (first 3)
                    authors = entry.findall('atom:author', ns)
                    author_names = [a.find('atom:name', ns).text for a in authors[:3]]
                    if len(authors) > 3:
                        author_str = f"{', '.join(author_names)} et al."
                    else:
                        author_str = ', '.join(author_names)
                    
                    # Enhanced description with authors
                    enhanced_description = f"[arXiv Paper] {author_str} — {summary[:300]}..."
                    
                    item = NewsItem(
                        url=link,
                        title=f"📄 {title}",  # Add paper emoji
                        description=enhanced_description,
                        source='arxiv',
                        published_at=pub_date,
                    )
                    
                    all_items.append(item)
                
                except Exception as e:
                    logger.warning(f"Error parsing arXiv entry: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching arXiv for query '{query}': {e}")
            continue
    
    logger.info(f"arXiv: Fetched {len(all_items)} papers")
    return all_items
