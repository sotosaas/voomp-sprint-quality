"""File-based cache repository.

Provides persistent caching across restarts with TTL support.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class CacheRepository:
    """File-based cache with TTL support.
    
    Cache files are stored as JSON in a .cache directory.
    Each entry has a timestamp for TTL validation.
    """

    def __init__(self, cache_dir: Path | str, default_ttl: int = 900) -> None:
        """Initialize cache repository.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (15 minutes)
        """
        self._cache_dir = Path(cache_dir)
        self._default_ttl = default_ttl

    def _get_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace(" ", "_").replace(":", "_")
        return self._cache_dir / f"{safe_key}.json"

    def get(self, key: str, ttl: int | None = None) -> Any | None:
        """Get cached value if fresh enough.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            Cached data or None if expired/missing
        """
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        # Check TTL
        ttl = ttl or self._default_ttl
        age = time.time() - payload.get("timestamp", 0)
        if age > ttl:
            return None

        return payload.get("data")

    def set(self, key: str, data: Any) -> bool:
        """Store data in cache.
        
        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
            
        Returns:
            True if successful, False otherwise
        """
        self._cache_dir.mkdir(exist_ok=True)
        path = self._get_path(key)

        payload = {
            "timestamp": time.time(),
            "data": data,
        }

        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, default=str)
            return True
        except IOError:
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        path = self._get_path(key)
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False

    def clear(self) -> int:
        """Delete all cache entries.
        
        Returns:
            Number of files deleted
        """
        count = 0
        if self._cache_dir.exists():
            for f in self._cache_dir.glob("*.json"):
                try:
                    f.unlink()
                    count += 1
                except IOError:
                    pass
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self._cache_dir.exists():
            return {"total_entries": 0, "total_size_bytes": 0}

        files = list(self._cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_entries": len(files),
            "total_size_bytes": total_size,
            "cache_dir": str(self._cache_dir),
        }
