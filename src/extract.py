import logging
from pathlib import Path

import requests

from config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB


def _download(url: str, dest: Path) -> Path:
    if dest.exists():
        logger.info("Skipping download, already exists: %s", dest)
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest.with_suffix(dest.suffix + ".part")

    logger.info("Downloading %s -> %s", url, dest)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)

    tmp_path.rename(dest)
    logger.info("Downloaded %s (%.1f MB)", dest.name, dest.stat().st_size / 1_000_000)
    return dest


def extract() -> tuple[Path, Path]:
    trip_path = _download(settings.TRIP_DATA_URL, settings.TRIP_DATA_RAW_PATH)
    zone_path = _download(settings.ZONE_LOOKUP_URL, settings.ZONE_LOOKUP_RAW_PATH)
    return trip_path, zone_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extract()
