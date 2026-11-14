"""
FastAPI dependencies.
Provides singleton access to ZuhuraScienceAccess and configuration dependencies.
"""

from functools import lru_cache
from pathlib import Path
from zuhura.core.config import settings
from zuhura_data.access.client import ZuhuraScienceAccess


@lru_cache()
def get_science_access() -> ZuhuraScienceAccess:
    """Dependency provider for ZuhuraScienceAccess client."""
    repo_root = Path(settings.DATA_REPO_ROOT)
    catalog_path = repo_root / "catalogs/zuhura_science_catalog.json"
    return ZuhuraScienceAccess(catalog_path=catalog_path, repo_root=repo_root)
