from .base import Collector
from .dataset import DatasetCollector
from .demo_sites import DemoSitesCollector
from .open_web import OpenWebCollector
from .youtube import TikTokCollector, YouTubeCollector

REGISTRY: dict[str, type[Collector]] = {
    "dataset": DatasetCollector,
    "demo_sites": DemoSitesCollector,
    "open_web": OpenWebCollector,
    "youtube": YouTubeCollector,
    "tiktok": TikTokCollector,
}

__all__ = ["Collector", "REGISTRY"]
