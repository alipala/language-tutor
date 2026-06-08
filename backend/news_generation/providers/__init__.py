"""News provider abstractions (Phase 1 onwards)."""

from news_generation.providers.base import BaseNewsProvider
from news_generation.providers.newsapi import NewsApiProvider
from news_generation.providers.newsdata import NewsDataProvider
from news_generation.providers.google_news_rss import GoogleNewsRssProvider
from news_generation.providers.gdelt import GdeltProvider
from news_generation.providers.types import (
    CategoryDescriptor,
    DescriptorKind,
    FetchReason,
    ProviderResult,
)

__all__ = [
    "BaseNewsProvider",
    "NewsApiProvider",
    "NewsDataProvider",
    "GoogleNewsRssProvider",
    "GdeltProvider",
    "CategoryDescriptor",
    "DescriptorKind",
    "FetchReason",
    "ProviderResult",
]
