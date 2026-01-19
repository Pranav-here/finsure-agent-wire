import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from agentwire.config import get_settings  # noqa: E402
from agentwire.models import Item  # noqa: E402
from agentwire.scoring import score_item  # noqa: E402


def main() -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    samples = [
        "Bank tests multi-agent AI for real-time fraud checks",
        "Insurance startup rolls out agentic underwriting assistant",
        "Celebrity breaks silence on sports agents drama",
        "Autonomous trading agents hit hedge fund desk",
        "LangGraph workflow improves claims triage for insurtech",
    ]
    print("Scoring samples with current keyword settings:")
    for title in samples:
        item = Item(source="sample", title=title, description="", url="http://example.com", published_at=now)
        score = score_item(item, settings)
        print(f"- {title} -> {score}")


if __name__ == "__main__":
    main()
