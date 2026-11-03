"""data_processor.py

Optimized data processing with parallel fetching and aggressive caching.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import pandas as pd

from config import CACHE_TTL_SECONDS, PROJECTS, JIRA_URL
from jira_client import JiraClient

# ------------------------------------------------------------------
# Cache helpers — file-based for persistence across restarts
# ------------------------------------------------------------------

CACHE_DIR = Path(__file__).parent / ".cache"


def _cache_path(key: str) -> Path:
    safe_key = key.replace("/", "_").replace(" ", "_").replace(":", "_")
    return CACHE_DIR / f"{safe_key}.json"


def _read_cache(key: str, ttl: int | None = None) -> list[dict] | None:
    """Read cached data if fresh enough."""
    path = _cache_path(key)
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    ttl = ttl or CACHE_TTL_SECONDS
    age = time.time() - payload.get("timestamp", 0)
    if age > ttl:
        return None

    return payload.get("data")


def _write_cache(key: str, data: list[dict] | dict) -> None:
    """Persist data to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    path = _cache_path(key)
    payload = {"timestamp": time.time(), "data": data}
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, default=str)
    except IOError:
        pass  # Fail silently on write errors


def clear_cache() -> None:
    """Delete all cached files."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
            except IOError:
                pass


# ------------------------------------------------------------------
# Optimized data fetchers
# ------------------------------------------------------------------

def fetch_sprint_issues(
    project_key: str,
    sprint_id: int,
    sprint_name: str = "",
    force_refresh: bool = False,
) -> list[dict]:
    """Fetch issues for a sprint with caching."""
    cache_key = f"{project_key}_sprint_{sprint_id}"

    if not force_refresh:
        cached = _read_cache(cache_key)
        if cached is not None:
            return cached

    client = JiraClient()
    issues = client.get_issues_in_sprint(sprint_id, project_key)
    _write_cache(cache_key, issues)
    return issues


def fetch_sprints_issues_batch(
    project_key: str,
    sprints: list[dict],
    force_refresh: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[int, list[dict]]:
    """Fetch issues for multiple sprints — uses cache first, then parallel fetch.
    
    This is the main performance optimization: instead of sequential API calls,
    we first check cache for all sprints, then fetch missing ones in parallel.
    """
    results: dict[int, list[dict]] = {}
    to_fetch: list[dict] = []
    
    # Phase 1: Check cache for all sprints
    for sprint in sprints:
        cache_key = f"{project_key}_sprint_{sprint['id']}"
        if not force_refresh:
            cached = _read_cache(cache_key)
            if cached is not None:
                results[sprint["id"]] = cached
                continue
        to_fetch.append(sprint)
    
    # Phase 2: Parallel fetch for cache misses
    if to_fetch:
        client = JiraClient()
        fetched = client.get_issues_for_sprints_parallel(
            to_fetch,
            project_key,
            progress_callback=progress_callback,
            max_workers=5,
        )
        
        # Cache the fetched results
        for sprint_id, issues in fetched.items():
            cache_key = f"{project_key}_sprint_{sprint_id}"
            _write_cache(cache_key, issues)
            results[sprint_id] = issues
    
    return results


def fetch_last_30_days(
    project_key: str,
    force_refresh: bool = False,
) -> list[dict]:
    """Fetch issues delivered in the last 30 days."""
    cache_key = f"{project_key}_last30days"

    if not force_refresh:
        cached = _read_cache(cache_key)
        if cached is not None:
            return cached

    client = JiraClient()
    issues = client.get_issues_in_date_range(project_key, days=30)
    _write_cache(cache_key, issues)
    return issues


# ------------------------------------------------------------------
# DataFrame builders
# ------------------------------------------------------------------

def _issues_to_rows(issues: list[dict], project_key: str, sprint_id: int | None, sprint_name: str) -> list[dict]:
    """Convert normalized issues to DataFrame rows."""
    base_url = JIRA_URL.rstrip("/")
    rows = []
    
    for issue in issues:
        if issue.get("is_subtask", False):
            continue
        rows.append({
            "key": issue["key"],
            "summary": issue["summary"],
            "assignee_name": issue["assignee_name"],
            "assignee_email": issue["assignee_email"],
            "project_key": project_key,
            "project_name": PROJECTS.get(project_key, project_key),
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "issue_type": issue["issue_type"],
            "sub_bug_count": issue["sub_bug_count"],
            "sub_bugs": issue.get("sub_bugs", []),
            "created": issue["created"],
            "resolution_date": issue["resolution_date"],
            "jira_url": f"{base_url}/browse/{issue['key']}",
        })
    
    return rows


def build_issues_dataframe(
    project_key: str,
    sprint_id: int,
    sprint_name: str = "",
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Build a DataFrame of issues for a single sprint."""
    issues = fetch_sprint_issues(project_key, sprint_id, sprint_name, force_refresh)

    if not issues:
        return _empty_dataframe()

    rows = _issues_to_rows(issues, project_key, sprint_id, sprint_name)
    if not rows:
        return _empty_dataframe()

    df = pd.DataFrame(rows)
    df["sub_bug_count"] = df["sub_bug_count"].fillna(0).astype(int)
    df["created"] = pd.to_datetime(df["created"], errors="coerce", utc=True)
    df["resolution_date"] = pd.to_datetime(df["resolution_date"], errors="coerce", utc=True)

    return df


def build_last_30_days_dataframe(
    project_key: str,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Build a DataFrame of issues delivered in the last 30 days."""
    issues = fetch_last_30_days(project_key, force_refresh)

    if not issues:
        return _empty_dataframe()

    rows = _issues_to_rows(issues, project_key, None, "Últimos 30 dias")
    if not rows:
        return _empty_dataframe()

    df = pd.DataFrame(rows)
    df["sub_bug_count"] = df["sub_bug_count"].fillna(0).astype(int)
    df["created"] = pd.to_datetime(df["created"], errors="coerce", utc=True)
    df["resolution_date"] = pd.to_datetime(df["resolution_date"], errors="coerce", utc=True)
    return df


def _empty_dataframe() -> pd.DataFrame:
    """Return an empty DataFrame with the expected schema."""
    return pd.DataFrame(columns=[
        "key", "summary", "assignee_name", "assignee_email",
        "project_key", "project_name", "sprint_id", "sprint_name",
        "issue_type", "sub_bug_count", "sub_bugs",
        "created", "resolution_date", "jira_url",
    ])


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

def get_dev_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Rank developers by quality score."""
    if df.empty:
        return pd.DataFrame(columns=[
            "assignee_name", "cards_delivered", "total_sub_bugs",
            "bug_ratio", "quality_score",
        ])

    grouped = (
        df.groupby("assignee_name", as_index=False)
        .agg(
            cards_delivered=("key", "count"),
            total_sub_bugs=("sub_bug_count", "sum"),
        )
    )

    grouped["bug_ratio"] = (
        grouped["total_sub_bugs"] / grouped["cards_delivered"]
    ).round(2)

    grouped["quality_score"] = (
        grouped["cards_delivered"] / (grouped["total_sub_bugs"] + 1)
    ).round(2)

    return (
        grouped
        .sort_values("quality_score", ascending=False)
        .reset_index(drop=True)
    )


def get_card_ranking(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Return cards with most sub-bugs."""
    if df.empty:
        return df

    cols = ["key", "summary", "assignee_name", "sub_bug_count", "issue_type", "jira_url"]
    return (
        df[cols]
        .query("sub_bug_count > 0")
        .sort_values("sub_bug_count", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def get_sprint_trend(
    project_key: str,
    last_n_sprints: int = 5,
    force_refresh: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> pd.DataFrame:
    """Build trend data across sprints — OPTIMIZED with parallel fetching."""
    client = JiraClient()
    board = client.get_board(project_key)
    if not board:
        return pd.DataFrame()

    current_year = datetime.now().year
    all_year_sprints = client.get_sprints(
        board["id"],
        state="active,closed",
        max_results=50,
        year=current_year,
    )
    
    sprints = all_year_sprints[-last_n_sprints:] if len(all_year_sprints) >= last_n_sprints else all_year_sprints
    if not sprints:
        return pd.DataFrame()

    # Parallel fetch all sprint issues at once
    sprint_issues = fetch_sprints_issues_batch(
        project_key,
        sprints,
        force_refresh=force_refresh,
        progress_callback=progress_callback,
    )

    rows = []
    for sprint in sprints:
        issues = sprint_issues.get(sprint["id"], [])
        # Filter out subtasks
        issues = [i for i in issues if not i.get("is_subtask", False)]
        
        total_cards = len(issues)
        total_bugs = sum(i.get("sub_bug_count", 0) for i in issues)
        cards_with_bugs = sum(1 for i in issues if i.get("sub_bug_count", 0) > 0)
        avg_bugs = round(total_bugs / total_cards, 2) if total_cards > 0 else 0.0
        bug_rate = round((cards_with_bugs / total_cards) * 100, 1) if total_cards > 0 else 0.0

        rows.append({
            "sprint_id": sprint["id"],
            "sprint_name": sprint["name"],
            "sprint_state": sprint.get("state", ""),
            "total_cards": total_cards,
            "total_sub_bugs": total_bugs,
            "cards_with_bugs": cards_with_bugs,
            "avg_bugs_per_card": avg_bugs,
            "bug_rate_pct": bug_rate,
        })

    return pd.DataFrame(rows)


def get_last_30_days_summary(
    project_key: str,
    force_refresh: bool = False,
) -> dict:
    """Compute summary stats for the last 30 days."""
    df = build_last_30_days_dataframe(project_key, force_refresh)

    base = {
        "project_key": project_key,
        "project_name": PROJECTS.get(project_key, project_key),
    }

    if df.empty:
        return {
            **base,
            "total_cards": 0,
            "total_sub_bugs": 0,
            "cards_with_bugs": 0,
            "avg_bugs_per_card": 0.0,
            "bug_rate_pct": 0.0,
            "top_dev": "—",
            "top_dev_score": 0.0,
        }

    ranking = get_dev_ranking(df)
    top_dev = ranking.iloc[0]["assignee_name"] if not ranking.empty else "—"
    top_dev_score = float(ranking.iloc[0]["quality_score"]) if not ranking.empty else 0.0

    return {
        **base,
        "total_cards": len(df),
        "total_sub_bugs": int(df["sub_bug_count"].sum()),
        "cards_with_bugs": int((df["sub_bug_count"] > 0).sum()),
        "avg_bugs_per_card": round(float(df["sub_bug_count"].mean()), 2),
        "bug_rate_pct": round(float((df["sub_bug_count"] > 0).mean() * 100), 1),
        "top_dev": top_dev,
        "top_dev_score": round(top_dev_score, 2),
    }
