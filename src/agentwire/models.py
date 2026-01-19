from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Optional
from urllib.parse import parse_qsl, urlparse, urlunparse, urlencode


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
    "ref",
}


def canonicalize_url(url: str) -> str:
    """Normalize URL and drop tracking params to improve dedupe."""
    if not url:
        return url
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    filtered_query = sorted(
        [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS],
        key=lambda kv: kv[0],
    )
    query = urlencode(filtered_query, doseq=True)
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def url_hash(url: str) -> str:
    canon = canonicalize_url(url)
    return sha256(canon.encode("utf-8")).hexdigest()


@dataclass
class Item:
    source: str
    title: str
    description: Optional[str]
    url: str
    published_at: datetime
    score: Optional[float] = None
    domain: Optional[str] = None

    def canonical_url(self) -> str:
        return canonicalize_url(self.url)
