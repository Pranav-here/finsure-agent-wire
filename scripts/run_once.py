#!/usr/bin/env python3
"""
Main entry point for the news autoposter.

Run this script to execute one cycle of:
1. Collect news from GDELT, YouTube, RSS
2. Score and filter by relevance
3. Deduplicate against posted history
4. Post top items to X (Twitter)
"""

import logging
import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finsure_agent_wire.config import get_config
from finsure_agent_wire.pipeline import run_pipeline


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def main() -> None:
    """Main entry point."""
    # Load config
    config = get_config()
    
    # Setup logging
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Run the pipeline
        run_pipeline(config)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting.")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
