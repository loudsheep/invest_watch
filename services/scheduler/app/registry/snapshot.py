"""Writes data/registry_knf.json from the live KNF lists, used as the offline fallback.
Run from the repository root: python -m app.registry.snapshot data/registry_knf.json"""
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .knf import PROVIDERS


def main(target: str) -> None:
    providers = {}
    with httpx.Client() as client:
        for name, fetch in PROVIDERS.items():
            providers[name] = fetch(client)
            print(f"{name}: {len(providers[name])}")
    Path(target).write_text(
        json.dumps({"fetched_at": datetime.now(UTC).isoformat(), "providers": providers}, ensure_ascii=False, indent=1)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(sys.argv[1])
