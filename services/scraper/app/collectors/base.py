"""Common collector interface (ADR-0003): Collector -> RawDocument.

Every source plugin implements `discover` (find candidate URLs/items) and
`fetch` (turn one candidate into a RawDocument). Adding a source means
adding one subclass here and one row in the `sources` table / config/sources.yaml.
"""
from abc import ABC, abstractmethod
from collections.abc import Iterator

from investwatch_common.schemas import RawDocument


class Collector(ABC):
    name: str

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def discover(self) -> Iterator[str]:
        """Yield candidate identifiers (URLs, video ids, file paths) to fetch."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, candidate: str) -> RawDocument | None:
        """Fetch one candidate and normalize it into a RawDocument, or None if unavailable."""
        raise NotImplementedError
